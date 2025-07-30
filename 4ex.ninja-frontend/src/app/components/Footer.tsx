export default function Footer() {
  const currentYear: number = new Date().getFullYear();

  return (
    <footer className="bg-black border-t border-gray-800 p-6">
      <div className="container mx-auto">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="text-sm text-gray-400 text-center">
            <p>&copy; {currentYear} 4ex.ninja | Made by a Ninja</p>
            <p className="mt-2">
              Trading forex carries high risk. Past performance does not guarantee future results.
            </p>
          </div>

          <div className="flex space-x-4 text-xs text-gray-500">
            <a href="/terms" className="hover:text-white transition-colors">
              Terms of Service
            </a>
            <span>•</span>
            <a href="/privacy" className="hover:text-white transition-colors">
              Privacy Policy
            </a>
            <span>•</span>
            <a href="/disclaimer" className="hover:text-white transition-colors">
              Risk Disclaimer
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
