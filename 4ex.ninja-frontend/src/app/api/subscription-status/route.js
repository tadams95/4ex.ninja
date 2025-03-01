import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/auth-options"; // Import from the correct path
import { connectToDatabase } from "@/utils/mongodb";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session || !session.user) {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    const { db } = await connectToDatabase();
    // Use case-insensitive email query
    const user = await db
      .collection("users")
      .findOne({ 
        email: { $regex: `^${session.user.email}$`, $options: "i" } 
      });

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    //output user object for debugging
    console.log("User object:", user);

    // Simply use the isSubscribed boolean from MongoDB
    const hasActiveSubscription = user.isSubscribed === true;

    return NextResponse.json({
      isSubscribed: hasActiveSubscription,
      // Include these fields for compatibility with existing code
      subscriptionEnds: null,
      userEmail: user.email
    });
  } catch (error) {
    console.error("Error fetching subscription status:", error);
    return NextResponse.json(
      { error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
