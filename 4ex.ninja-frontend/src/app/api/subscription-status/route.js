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
      console.error("User not found in DB:", session.user.email);
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    // Log full user object for debugging
    console.log("Full user object from MongoDB:", {
      id: user._id.toString(),
      email: user.email,
      name: user.name,
      isSubscribed: user.isSubscribed,
      subscriptionStatus: typeof user.isSubscribed === 'boolean' ? 'boolean' : typeof user.isSubscribed
    });

    // Explicitly convert to boolean in case it's stored differently
    const hasActiveSubscription = Boolean(user.isSubscribed);

    return NextResponse.json({
      isSubscribed: hasActiveSubscription,
      // Include these fields for compatibility with existing code
      subscriptionEnds: null,
      userEmail: user.email,
      // Add debug info
      rawIsSubscribed: user.isSubscribed
    });
  } catch (error) {
    console.error("Error fetching subscription status:", error);
    return NextResponse.json(
      { error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
