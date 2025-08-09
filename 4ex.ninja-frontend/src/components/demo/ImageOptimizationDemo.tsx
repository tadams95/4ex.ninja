import OptimizedImage, { AvatarImage, HeroImage, IconImage } from '@/components/ui/OptimizedImage';

/**
 * Demo component showcasing optimized image usage
 * This demonstrates proper implementation of WebP/AVIF support with fallbacks
 */
export default function ImageOptimizationDemo() {
  return (
    <div className="space-y-8 p-6">
      <h2 className="text-2xl font-bold mb-4">Image Optimization Examples</h2>

      {/* Hero Image Example */}
      <section>
        <h3 className="text-lg font-semibold mb-2">Hero Image (Priority Loading)</h3>
        <div className="relative aspect-video w-full max-w-2xl">
          <HeroImage
            src="/next.svg"
            alt="Next.js Logo"
            fill
            className="object-contain"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        </div>
      </section>

      {/* Standard Optimized Images */}
      <section>
        <h3 className="text-lg font-semibold mb-2">Standard Images (Lazy Loading)</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <OptimizedImage
            src="/vercel.svg"
            alt="Vercel Logo"
            width={200}
            height={100}
            className="bg-white p-4 rounded"
          />
          <OptimizedImage
            src="/file.svg"
            alt="File Icon"
            width={200}
            height={100}
            className="bg-gray-100 p-4 rounded"
          />
          <OptimizedImage
            src="/globe.svg"
            alt="Globe Icon"
            width={200}
            height={100}
            className="bg-gray-100 p-4 rounded"
          />
          <OptimizedImage
            src="/window.svg"
            alt="Window Icon"
            width={200}
            height={100}
            className="bg-gray-100 p-4 rounded"
          />
        </div>
      </section>

      {/* Avatar Images */}
      <section>
        <h3 className="text-lg font-semibold mb-2">Avatar Images</h3>
        <div className="flex gap-4 items-center">
          <AvatarImage src="/favicon.ico" alt="User Avatar" size={40} />
          <AvatarImage src="/favicon.ico" alt="User Avatar" size={64} />
          <AvatarImage src="/favicon.ico" alt="User Avatar" size={80} />
        </div>
      </section>

      {/* Icon Images */}
      <section>
        <h3 className="text-lg font-semibold mb-2">Icon Images</h3>
        <div className="flex gap-4 items-center">
          <IconImage src="/file.svg" alt="File" size={16} />
          <IconImage src="/globe.svg" alt="Globe" size={24} />
          <IconImage src="/window.svg" alt="Window" size={32} />
        </div>
      </section>

      {/* Performance Info */}
      <section className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">Optimization Features</h3>
        <ul className="space-y-1 text-sm text-gray-600">
          <li>✅ WebP/AVIF format support with fallbacks</li>
          <li>✅ Responsive sizing with proper breakpoints</li>
          <li>✅ Lazy loading for non-critical images</li>
          <li>✅ Priority loading for above-the-fold images</li>
          <li>✅ Blur placeholder for smooth loading</li>
          <li>✅ Optimized quality settings per use case</li>
          <li>✅ Service Worker caching for faster subsequent loads</li>
        </ul>
      </section>
    </div>
  );
}
