import getStripe from "./get-stripe";

/**
 * Handles the Stripe checkout flow
 * @returns {Promise} Resolves when checkout is initiated
 */
export async function handleCheckout() {
  try {
    const response = await fetch("/api/create-checkout-session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Debug logging
    console.log("Response status:", response.status);
    
    // Get response content type
    const contentType = response.headers.get("content-type");

    // Parse response based on content type
    let responseData;
    if (contentType && contentType.includes("application/json")) {
      responseData = await response.json();
    } else {
      const text = await response.text();
      console.error("Unexpected response type:", contentType);
      console.error("Response text:", text);
      throw new Error("Server returned invalid response format");
    }

    if (!response.ok) {
      throw new Error(
        responseData.error || `HTTP error! status: ${response.status}`
      );
    }

    const stripe = await getStripe();
    if (!stripe) {
      throw new Error("Stripe failed to initialize");
    }

    const { error } = await stripe.redirectToCheckout({
      sessionId: responseData.id,
    });

    if (error) {
      console.error("Stripe redirect error:", error);
      throw error;
    }
    
    return true;
  } catch (error) {
    console.error("Checkout error:", error);
    throw error;
  }
}
