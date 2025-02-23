export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>

      <div className="space-y-6 text-gray-300">
        <section>
          <h2 className="text-xl font-bold mb-3">1. Service Description</h2>
          <p>
            4ex.ninja provides algorithmic forex trading signals through a
            subscription-based service. Our signals are generated using
            technical analysis and are provided for informational purposes only.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">2. Subscription Terms</h2>
          <p>
            Access to our signals requires an active subscription. Subscriptions
            are billed on a monthly basis and can be cancelled at any time.
            Refunds are provided at our discretion.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">3. Risk Disclosure</h2>
          <p>
            Forex trading involves substantial risk. Our signals do not
            guarantee profits. Users are solely responsible for their trading
            decisions and potential losses.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">4. Service Availability</h2>
          <p>
            While we strive for 24/7 availability, we cannot guarantee
            uninterrupted access to our services. Technical issues, market
            conditions, or maintenance may affect signal delivery.
          </p>
        </section>
      </div>
    </div>
  );
}
