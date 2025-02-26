import { NextResponse } from "next/server";
import Stripe from "stripe";
import { MongoClient } from "mongodb";
import crypto from "crypto";

// Initialize Stripe
const getStripeInstance = () => {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key || typeof key !== "string") {
    throw new Error("Invalid or missing STRIPE_SECRET_KEY");
  }
  return new Stripe(key, {
    apiVersion: "2023-10-16",
  });
};

const stripe = getStripeInstance();

// MongoDB connection
const getMongoClient = async () => {
  const uri = process.env.MONGO_CONNECTION_STRING;
  if (!uri) {
    throw new Error("Missing MongoDB connection string");
  }
  
  const client = new MongoClient(uri);
  await client.connect();
  return client;
};

// Simple password hashing without bcryptjs
const hashPassword = (password) => {
  return crypto
    .createHash('sha256')
    .update(password)
    .digest('hex');
};

export async function POST(request) {
  let client;
  try {
    const { sessionId } = await request.json();
    
    if (!sessionId) {
      return NextResponse.json({ error: "Session ID required" }, { status: 400 });
    }
    
    // Retrieve the checkout session to verify payment
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    
    if (!session) {
      return NextResponse.json({ error: "Invalid session" }, { status: 400 });
    }
    
    // Check if payment was successful
    if (session.payment_status !== "paid") {
      return NextResponse.json({ 
        error: `Payment not completed. Status: ${session.payment_status}` 
      }, { status: 400 });
    }
    
    // Get customer details from Stripe
    const customerId = session.customer;
    const customer = await stripe.customers.retrieve(customerId);
    
    if (!customer || !customer.email) {
      return NextResponse.json({ error: "Customer information missing" }, { status: 400 });
    }
    
    // Connect to MongoDB
    client = await getMongoClient();
    const db = client.db("4ex-ninja");
    const usersCollection = db.collection("User");
    
    // Check if user already exists
    const email = customer.email;
    const existingUser = await usersCollection.findOne({ email });
    
    if (!existingUser) {
      // Generate a random password
      const generatedPassword = Math.random().toString(36).slice(-8);
      const hashedPassword = hashPassword(generatedPassword);
      
      // Create a new user
      await usersCollection.insertOne({
        email,
        password: hashedPassword,
        stripeCustomerId: customerId,
        isActive: true,
        subscriptionEndDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
        createdAt: new Date(),
        updatedAt: new Date()
      });
      
      // Return both email and generated password for auto login
      return NextResponse.json({ 
        email, 
        password: generatedPassword,
        message: "Account created successfully" 
      });
    }
    
    // If user exists, update their subscription status
    const tempPassword = Math.random().toString(36).slice(-8);
    const hashedPassword = hashPassword(tempPassword);
    
    await usersCollection.updateOne(
      { email },
      { 
        $set: {
          isActive: true,
          password: hashedPassword,
          subscriptionEndDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
          updatedAt: new Date()
        }
      }
    );
    
    return NextResponse.json({ 
      email, 
      password: tempPassword,
      message: "Subscription updated successfully" 
    });
    
  } catch (error) {
    console.error("Verification error:", error);
    return NextResponse.json({ error: error.message || "Internal server error" }, { status: 500 });
  } finally {
    if (client) {
      await client.close();
    }
  }
}
