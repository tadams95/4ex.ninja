export default function DisclaimerPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">Risk Disclaimer</h1>

      <div className="space-y-6 text-gray-300">
        <section>
          <h2 className="text-xl font-bold mb-3">High Risk Warning</h2>
          <p>
            Foreign exchange trading carries a high level of risk and may not be suitable for all
            investors. The high degree of leverage can work against you as well as for you. Before
            deciding to trade foreign exchange you should carefully consider your investment
            objectives, level of experience, and risk appetite.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">No Guaranteed Returns</h2>
          <p>
            The insights and recommendations provided by 4ex.ninja are based on technical analysis
            and historical data. Past performance is not indicative of future results. No
            representation is being made that any account will or is likely to achieve profits or
            losses similar to those discussed on our platform.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Independent Financial Advice</h2>
          <p>
            Our trading insights and recommendations should not be construed as financial advice. We
            strongly recommend consulting with a qualified financial advisor before making any
            investment decisions. You should be aware that you may sustain a loss of some or all of
            your investment capital.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Recommendation Accuracy</h2>
          <p>
            While we strive to provide accurate and timely trading insights and recommendations, we
            cannot guarantee their accuracy or timeliness. Market conditions can change rapidly, and
            delays in recommendation delivery or execution may affect actual results.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold mb-3">Risk Management</h2>
          <p>
            You should never trade with money you cannot afford to lose. We recommend using strict
            money management principles and never risking more than a small percentage of your
            trading capital on any single trade.
          </p>
        </section>

        <section className="bg-gray-800 p-6 rounded-lg mt-8">
          <h2 className="text-xl font-bold mb-3 text-red-700">Important Notice</h2>
          <p>
            By using our services, you acknowledge that you have read, understood, and agree to
            these risk warnings. If you do not agree with these terms, please do not use our
            services.
          </p>
        </section>
      </div>
    </div>
  );
}
