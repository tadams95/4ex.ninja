import { NextResponse } from "next/server";
import { MongoClient, ObjectId } from "mongodb";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/auth-options";

export async function POST() {
  try {
    // Get the current session to verify the user
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 401 }
      );
    }

    // Connect to MongoDB
    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);
    
    try {
      await client.connect();
      const db = client.db("4ex_users");
      const usersCollection = db.collection("users");
      
      // Find the user by ID
      const user = await usersCollection.findOne({
        _id: new ObjectId(session.user.id)
      });

      if (!user) {
        return NextResponse.json(
          { error: "User not found" },
          { status: 404 }
        );
      }

      // If the user has a subscription with Stripe, you would cancel it here
      // For example:
      // if (user.customerStripeId && user.subscriptionId) {
      //   const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
      //   await stripe.subscriptions.update(user.subscriptionId, {
      //     cancel_at_period_end: true
      //   });
      // }

      // Update the user in MongoDB to reflect cancellation at period end
      // We keep isSubscribed as true until the subscription actually ends
      await usersCollection.updateOne(
        { _id: new ObjectId(session.user.id) },
        { 
          $set: { 
            canceledAt: new Date(),
            willCancelAtPeriodEnd: true
          } 
        }
      );

      return NextResponse.json({
        message: "Subscription will be canceled at the end of the current billing period."
      });
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error("Error cancelling subscription:", error);
    return NextResponse.json(
      { error: "Failed to cancel subscription" },
      { status: 500 }
    );
  }
}
