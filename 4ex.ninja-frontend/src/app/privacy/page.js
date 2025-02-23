export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>

      <div className="space-y-6 text-gray-300">
        <section>
          <h2 className="text-xl font-bold mb-3">Information We Collect</h2>
          <p>
            We collect basic account information including email addresses and
            subscription status. Payment processing is handled securely through
            Stripe.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">How We Use Your Data</h2>
          <ul className="list-disc pl-5 space-y-2">
            <li>To provide and maintain our service</li>
            <li>To notify you about changes to our service</li>
            <li>To provide customer support</li>
            <li>To process your payments</li>
          </ul>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Data Protection</h2>
          <p>
            We implement industry-standard security measures to protect your
            personal information. We never share or sell your data to third
            parties.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Cookies Policy</h2>
          <p>
            We use essential cookies to maintain your session and preferences.
            You can control cookie settings through your browser.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Contact Us</h2>
          <p>
            For any privacy-related questions, please contact us at
            privacy@4ex.ninja
          </p>
        </section>
      </div>
    </div>
  );
}
