export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>

      <div className="space-y-6 text-gray-300">
        <section>
          <h2 className="text-xl font-bold mb-3">1. Service Description</h2>
          <p>
            4ex.ninja provides algorithmic forex trading insights and recommendations through a
            token-based service. Our insights are generated using technical analysis and are
            provided for informational purposes only.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">2. Token Terms</h2>
          <p>
            Access to our insights and recommendations requires tokens. Tokens are purchased and
            utilized when accessing premium features and recommendations. Token purchases occur on
            the market and are not controlled by 4ex.ninja.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">3. Risk Disclosure</h2>
          <p>
            Forex trading involves substantial risk. Our insights and recommendations do not
            guarantee profits. Users are solely responsible for their trading decisions and
            potential losses.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">4. Service Availability</h2>
          <p>
            While we strive for 24/7 availability, we cannot guarantee uninterrupted access to our
            services. Technical issues, market conditions, or maintenance may affect insight and
            recommendation delivery.
          </p>
        </section>
      </div>
    </div>
  );
}
