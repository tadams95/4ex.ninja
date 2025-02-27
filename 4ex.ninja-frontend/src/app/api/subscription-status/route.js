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
    // Access the users collection in the 4ex_users database
    const user = await db
      .collection("users")
      .findOne({ email: session.user.email });

    if (!user) {
      return NextResponse.json({ error: "User not found" }, { status: 404 });
    }

    return NextResponse.json({
      isSubscribed:
        !!user.subscriptionEnds && new Date(user.subscriptionEnds) > new Date(),
      subscriptionEnds: user.subscriptionEnds || null,
    });
  } catch (error) {
    console.error("Error fetching subscription status:", error);
    return NextResponse.json(
      { error: "Failed to fetch subscription status" },
      { status: 500 }
    );
  }
}
