# Stripe Webhook Configuration Guide

This document explains how to configure Stripe webhooks for our subscription system.

## Setup Steps

1. Log in to your [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers > Webhooks**
3. Click **Add Endpoint**
4. Enter your webhook URL:
   - For local development: Use a tunneling service like ngrok to exupose your local server
   - For production: `https://4ex.ninja/api/webhook/stripe`
5. Select the following events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Click **Add Endpoint** to create the webhook

## Environment Variables

Add these variables to your `.env` file:

```
STRIPE_SECRET_KEY=sk_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
MONGO_CONNECTION_STRING=mongodb+srv://...
```

The webhook secret can be found in your Stripe Dashboard under the webhook settings.

## Testing Webhooks Locally

1. Install the Stripe CLI from [https://stripe.com/docs/stripe-cli](https://stripe.com/docs/stripe-cli)
2. Log in with `stripe login`
3. Forward events to your local server:

```
stripe listen --forward-to localhost:3000/api/webhook/stripe
```

4. In another terminal, trigger test events:

```
stripe trigger checkout.session.completed
```

## Verifying Webhook Configuration

After setting up webhooks:

1. Make a test subscription purchase
2. Check your server logs to confirm the webhook was received
3. Verify that the user document in MongoDB was updated with subscription details
