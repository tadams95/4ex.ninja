import { NextResponse } from "next/server";
import Stripe from "stripe";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";

// Check if Stripe key exists before initializing
const stripeKey = process.env.STRIPE_SECRET_KEY;
const stripe = stripeKey
  ? new Stripe(stripeKey, { apiVersion: "2023-10-16" })
  : null;

// Validate MongoDB connection string exists
const mongoUri = process.env.MONGO_CONNECTION_STRING;
let mongoClient = null;

// Function to safely connect to MongoDB
async function connectToMongo() {
  try {
    if (!mongoUri) {
      return { error: "MongoDB connection string is not defined" };
    }

    if (!mongoClient) {
      mongoClient = new MongoClient(mongoUri);
    }

    await mongoClient.connect();
    const db = mongoClient.db("4ex_users");  // Updated to match the correct DB name
    return { db };
  } catch (error) {
    console.error("MongoDB connection error:", error);
    return { error: `Failed to connect to MongoDB: ${error.message}` };
  }
}

export async function POST(request) {
  try {
    // Check if Stripe is initialized
    if (!stripe) {
      return NextResponse.json(
        { error: "Stripe API key is not configured" },
        { status: 500 }
      );
    }

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

    // Connect to MongoDB
    const conn = await connectToMongo();
    if (conn.error) {
      return NextResponse.json({ error: conn.error }, { status: 500 });
    }

    const { db } = conn;
    const usersCollection = db.collection("users");  // Updated to match the correct collection name

    // Generate a temporary password and hash it
    const tempPassword = Math.random().toString(36).slice(-8);
    const hashedPassword = await bcrypt.hash(tempPassword, 10);

    // Create or update user record
    // Note: The webhook will handle the complete subscription details
    await usersCollection.updateOne(
      { email },
      {
        $set: {
          email,
          password: hashedPassword,
          updatedAt: new Date(),
        },
        $setOnInsert: {
          createdAt: new Date(),
        },
      },
      { upsert: true }
    );

    return NextResponse.json({
      success: true,
      message: "User registered successfully",
      // Only return password in development, never in production
      temporaryPassword:
        process.env.NODE_ENV === "development" ? tempPassword : undefined,
    });
  } catch (error) {
    console.error("Subscription error:", error);
    return NextResponse.json(
      { error: "Failed to process subscription" },
      { status: 500 }
    );
  } finally {
    // Close MongoDB connection if it exists
    if (mongoClient) {
      try {
        await mongoClient.close();
      } catch (err) {
        console.error("Error closing MongoDB connection:", err);
      }
    }
  }
}
