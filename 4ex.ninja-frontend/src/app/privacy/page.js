export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>

      <div className="space-y-6 text-gray-300">
        <section>
          <h2 className="text-xl font-bold mb-3">Information We Collect</h2>
          <p>
            None. 4ex.ninja does not collect any personal information from its users. We just check
            your token balance to provide the service.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Contact Us</h2>
          <p>For any privacy-related questions, please contact us at privacy@4ex.ninja</p>
        </section>
      </div>
    </div>
  );
}
