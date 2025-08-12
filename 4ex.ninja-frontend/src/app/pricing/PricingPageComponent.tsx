'use client';

export default function PricingPageComponent() {
  return (
    <div className="container mx-auto px-4 md:px-6 lg:px-8 py-8 max-w-4xl bg-black min-h-screen">
      <h1 className="text-3xl font-bold text-center mb-8 text-white">Choose Your Plan</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Free Plan */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Free</h2>
          <p className="text-3xl font-bold text-white mb-6">
            $0<span className="text-sm text-gray-400">/month</span>
          </p>
          <ul className="space-y-3 mb-6">
            <li className="text-gray-300">✓ Basic access</li>
            <li className="text-gray-300">✓ Limited features</li>
            <li className="text-gray-300">✓ Community support</li>
          </ul>
          <button className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors">
            Get Started
          </button>
        </div>

        {/* Pro Plan */}
        <div className="bg-gray-900 rounded-lg p-6 border border-green-500 relative">
          <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
            <span className="bg-green-500 text-black px-3 py-1 rounded-full text-sm font-semibold">
              Popular
            </span>
          </div>
          <h2 className="text-xl font-semibold text-white mb-4">Pro</h2>
          <p className="text-3xl font-bold text-white mb-6">
            $29<span className="text-sm text-gray-400">/month</span>
          </p>
          <ul className="space-y-3 mb-6">
            <li className="text-gray-300">✓ Full access</li>
            <li className="text-gray-300">✓ All features</li>
            <li className="text-gray-300">✓ Priority support</li>
            <li className="text-gray-300">✓ Advanced analytics</li>
          </ul>
          <button className="w-full bg-green-500 hover:bg-green-400 text-black py-2 px-4 rounded-lg transition-colors font-semibold">
            Start Pro Trial
          </button>
        </div>

        {/* Enterprise Plan */}
        <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Enterprise</h2>
          <p className="text-3xl font-bold text-white mb-6">Custom</p>
          <ul className="space-y-3 mb-6">
            <li className="text-gray-300">✓ Custom solutions</li>
            <li className="text-gray-300">✓ Dedicated support</li>
            <li className="text-gray-300">✓ SLA guarantees</li>
            <li className="text-gray-300">✓ Custom integrations</li>
          </ul>
          <button className="w-full bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors">
            Contact Sales
          </button>
        </div>
      </div>

      <div className="mt-12 text-center">
        <p className="text-gray-400">
          All plans include a 14-day free trial. No credit card required.
        </p>
      </div>
    </div>
  );
}
