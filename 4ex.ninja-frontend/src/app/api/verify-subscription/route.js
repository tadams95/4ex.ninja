import { NextResponse } from "next/server";
import Stripe from "stripe";
import { hash } from "bcryptjs";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

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

export async function POST(request) {
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
    
    // Check if user already exists
    const email = customer.email;
    let user = await prisma.user.findUnique({ where: { email } });
    
    if (!user) {
      // Generate a random password
      const generatedPassword = Math.random().toString(36).slice(-8);
      const hashedPassword = await hash(generatedPassword, 12);
      
      // Create a new user
      user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          stripeCustomerId: customerId,
          isActive: true, // Active subscription
          subscriptionEndDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days from now
        },
      });
      
      // Return both email and generated password for auto login
      return NextResponse.json({ 
        email, 
        password: generatedPassword,
        message: "Account created successfully" 
      });
    }
    
    // If user exists, update their subscription status
    await prisma.user.update({
      where: { id: user.id },
      data: {
        isActive: true,
        subscriptionEndDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
      }
    });
    
    // We don't know the user's password, so we need to set a temporary one for auto-login
    const tempPassword = Math.random().toString(36).slice(-8);
    const hashedPassword = await hash(tempPassword, 12);
    
    await prisma.user.update({
      where: { id: user.id },
      data: { password: hashedPassword }
    });
    
    return NextResponse.json({ 
      email, 
      password: tempPassword,
      message: "Subscription updated successfully" 
    });
    
  } catch (error) {
    console.error("Verification error:", error);
    return NextResponse.json({ error: error.message || "Internal server error" }, { status: 500 });
  }
}
