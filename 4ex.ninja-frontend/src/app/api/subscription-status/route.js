import { NextResponse } from "next/server";
import { MongoClient, ObjectId } from "mongodb";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/auth-options";

export async function GET() {
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

      // Map isSubscribed boolean to a status string
      const subscriptionStatus = user.isSubscribed ? "active" : "inactive";
      
      // Return subscription details
      return NextResponse.json({
        isSubscribed: user.isSubscribed || false,
        subscriptionStatus: subscriptionStatus,
        subscriptionId: user.subscriptionId || null,
        subscriptionEnds: user.subscriptionEnds || null,
        customerStripeId: user.customerStripeId || null
      });
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error("Error fetching subscription status:", error);
    return NextResponse.json(
      { error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
