import { NextResponse } from "next/server";
import Stripe from "stripe";
import { MongoClient } from "mongodb";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
  apiVersion: "2023-10-16",
});

const mongoClient = new MongoClient(process.env.MONGO_CONNECTION_STRING);

export async function POST(request) {
  try {
    const { email, sessionId } = await request.json();
    
    if (!email || !sessionId) {
      return NextResponse.json(
        { error: "Email and session ID are required" },
        { status: 400 }
      );
    }

    // Verify the Stripe session
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    
    if (!session || session.payment_status !== "paid") {
      return NextResponse.json(
        { error: "Invalid session or payment not completed" },
        { status: 400 }
      );
    }

    // Get subscription details
    const subscription = await stripe.subscriptions.retrieve(
      session.subscription
    );

    // Calculate subscription end date
    const subscriptionEnds = new Date(subscription.current_period_end * 1000);
    
    // Connect to MongoDB
    await mongoClient.connect();
    const db = mongoClient.db("users");
    const usersCollection = db.collection("subscribers");
    
    // Generate a temporary password (in production, use a secure method)
    const tempPassword = Math.random().toString(36).slice(-8);
    
    // Create or update user
    await usersCollection.updateOne(
      { email },
      { 
        $set: {
          email,
          subscriptionStatus: "active",
          subscriptionId: subscription.id,
          subscriptionEnds,
          customerStripeId: session.customer,
          password: tempPassword, // In a real app, hash this password
          updatedAt: new Date()
        },
        $setOnInsert: {
          createdAt: new Date()
        }
      },
      { upsert: true }
    );

    return NextResponse.json({ 
      success: true,
      message: "Subscription activated",
      // Only return password in development, never in production
      temporaryPassword: process.env.NODE_ENV === 'development' ? tempPassword : undefined
    });
    
  } catch (error) {
    console.error("Subscription error:", error);
    return NextResponse.json(
      { error: "Failed to process subscription" },
      { status: 500 }
    );
  } finally {
    await mongoClient.close();
  }
}
