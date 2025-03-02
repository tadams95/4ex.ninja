import { NextResponse } from "next/server";
import Stripe from "stripe";
import { MongoClient } from "mongodb";
import { headers } from "next/headers";

// Initialize Stripe with API key
const stripeKey = process.env.STRIPE_SECRET_KEY;
const stripe = stripeKey
  ? new Stripe(stripeKey, { apiVersion: "2023-10-16" })
  : null;

// Webhook secret for verifying events
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

// MongoDB connection
const mongoUri = process.env.MONGO_CONNECTION_STRING;
let mongoClient = null;

// Function to connect to MongoDB
async function connectToMongo() {
  try {
    if (!mongoUri) {
      return { error: "MongoDB connection string is not defined" };
    }

    if (!mongoClient) {
      mongoClient = new MongoClient(mongoUri);
    }

    await mongoClient.connect();
    const db = mongoClient.db("4ex_users");
    return { db };
  } catch (error) {
    console.error("MongoDB connection error:", error);
    return { error: `Failed to connect to MongoDB: ${error.message}` };
  }
}

// Function to update subscription status
async function updateSubscriptionStatus(event) {
  const conn = await connectToMongo();
  if (conn.error) {
    console.error(conn.error);
    return false;
  }

  const { db } = conn;
  const usersCollection = db.collection("users");
  
  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object;
        
        // Only handle subscription checkouts
        if (!session.subscription) return true;
        
        // Get subscription details
        const subscription = await stripe.subscriptions.retrieve(session.subscription);
        const customer = await stripe.customers.retrieve(session.customer);
        
        // Calculate subscription end date
        const subscriptionEnds = new Date(subscription.current_period_end * 1000);
        
        // Update user in database
        await usersCollection.updateOne(
          { email: customer.email },
          {
            $set: {
              subscriptionStatus: subscription.status,
              subscriptionId: subscription.id,
              subscriptionEnds,
              customerStripeId: session.customer,
              updatedAt: new Date(),
            },
          },
          { upsert: true }
        );
        
        console.log(`Updated subscription for ${customer.email}`);
        break;
      }
      
      case 'customer.subscription.updated':
      case 'customer.subscription.created': {
        const subscription = event.data.object;
        const customer = await stripe.customers.retrieve(subscription.customer);
        
        // Calculate subscription end date
        const subscriptionEnds = new Date(subscription.current_period_end * 1000);
        
        // Update user in database
        await usersCollection.updateOne(
          { email: customer.email },
          {
            $set: {
              subscriptionStatus: subscription.status,
              subscriptionId: subscription.id,
              subscriptionEnds,
              customerStripeId: subscription.customer,
              updatedAt: new Date(),
            },
          }
        );
        
        console.log(`Updated subscription for ${customer.email}: ${subscription.status}`);
        break;
      }
      
      case 'customer.subscription.deleted': {
        const subscription = event.data.object;
        const customer = await stripe.customers.retrieve(subscription.customer);
        
        // Update user in database to reflect canceled subscription
        await usersCollection.updateOne(
          { email: customer.email },
          {
            $set: {
              subscriptionStatus: 'canceled',
              subscriptionEnds: new Date(subscription.current_period_end * 1000),
              updatedAt: new Date(),
            },
          }
        );
        
        console.log(`Subscription canceled for ${customer.email}`);
        break;
      }
    }
    
    return true;
  } catch (error) {
    console.error('Error updating subscription status:', error);
    return false;
  } finally {
    if (mongoClient) {
      try {
        await mongoClient.close();
      } catch (err) {
        console.error("Error closing MongoDB connection:", err);
      }
    }
  }
}

// Main webhook handler
export async function POST(request) {
  try {
    if (!stripe || !webhookSecret) {
      return NextResponse.json(
        { error: "Stripe configuration missing" },
        { status: 500 }
      );
    }

    const body = await request.text();
    const headersList = headers();
    const signature = headersList.get("stripe-signature");

    if (!signature) {
      return NextResponse.json(
        { error: "Missing Stripe signature" },
        { status: 400 }
      );
    }

    // Verify event came from Stripe
    let event;
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (error) {
      console.error(`Webhook signature verification failed: ${error.message}`);
      return NextResponse.json(
        { error: "Invalid signature" },
        { status: 400 }
      );
    }

    // Handle the event
    const result = await updateSubscriptionStatus(event);
    
    if (!result) {
      return NextResponse.json(
        { error: "Failed to process event" },
        { status: 500 }
      );
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error("Webhook error:", error);
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 }
    );
  }
}
