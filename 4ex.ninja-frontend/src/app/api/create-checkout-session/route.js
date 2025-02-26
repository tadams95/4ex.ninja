import { NextResponse } from "next/server";
import Stripe from "stripe";

// Validate and initialize Stripe with better error handling
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

export async function POST() {
  try {
    // Validate environment variables
    const requiredEnvVars = [
      "STRIPE_SECRET_KEY",
      "STRIPE_PRICE_ID",
      "NEXT_PUBLIC_URL",
    ];

    for (const envVar of requiredEnvVars) {
      if (!process.env[envVar]) {
        console.error(`Missing ${envVar}`);
        return NextResponse.json(
          { error: `${envVar} is missing` },
          { status: 500 }
        );
      }
    }

    const session = await stripe.checkout.sessions.create({
      payment_method_types: ["card"],
      line_items: [
        {
          price: process.env.STRIPE_PRICE_ID,
          quantity: 1,
        },
      ],
      mode: "subscription",
      subscription_data: {
        trial_period_days: 30,
      },
      success_url: `https://${process.env.NEXT_PUBLIC_URL}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `https://${process.env.NEXT_PUBLIC_URL}/`,
    });

    return NextResponse.json({ id: session.id });
  } catch (error) {
    console.error("Stripe session creation error:", error);
    return NextResponse.json(
      { error: error.message || "Internal server error" },
      { status: 500 }
    );
  }
}
