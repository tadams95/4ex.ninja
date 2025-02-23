import SubscribeButton from "./components/SubscribeButton";

export default function Home() {
  return (
    // Add min-h-screen for full height and flex with centering classes
    <div className="min-h-screen flex items-center justify-center bg-black">
      <div className="container mx-auto px-4 py-8 text-center">
        <h1 className="text-4xl font-bold mb-6">Welcome to 4ex.ninja</h1>
        <p className="mb-4">
          Get access to premium forex signals and boost your trading strategy.
        </p>
        <SubscribeButton />
      </div>
    </div>
  );
}
