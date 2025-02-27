import { NextResponse } from "next/server";
import { MongoClient, ObjectId } from "mongodb";
import { getServerSession } from "next-auth/next";
import Stripe from "stripe";
import { authOptions } from "../auth/[...nextauth]/auth-options";

// Initialize Stripe
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY, {
  apiVersion: "2023-10-16",
});

export async function POST(request) {
  try {
    // Get current session to verify user
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: "You must be logged in to cancel your subscription" },
        { status: 401 }
      );
    }
    
    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);
    
    try {
      await client.connect();
      const db = client.db("users");
      const usersCollection = db.collection("subscribers");
      
      // Get user to check for stripeSubscriptionId
      const user = await usersCollection.findOne({ 
        _id: new ObjectId(session.user.id) 
      });
      
      if (!user) {
        return NextResponse.json(
          { error: "User not found" },
          { status: 404 }
        );
      }
      
      // If the user has a Stripe subscription, cancel it
      if (user.stripeSubscriptionId) {
        try {
          // Cancel at period end (doesn't immediately cancel)
          await stripe.subscriptions.update(user.stripeSubscriptionId, {
            cancel_at_period_end: true
          });
        } catch (stripeError) {
          console.error("Stripe cancellation error:", stripeError);
          // Continue with local updates even if Stripe fails
        }
      }
      
      // Update the user's subscription status
      await usersCollection.updateOne(
        { _id: new ObjectId(session.user.id) },
        { 
          $set: { 
            subscriptionStatus: "canceled",
            // Note: we're keeping subscriptionEnds as is, so they keep access until the end
            canceledAt: new Date()
          } 
        }
      );
      
      return NextResponse.json(
        { 
          message: "Subscription canceled successfully. You will have access until the end of your current billing period." 
        },
        { status: 200 }
      );
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error("Subscription cancellation error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 }
    );
  }
}
