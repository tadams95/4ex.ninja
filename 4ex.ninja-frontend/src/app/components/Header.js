import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-black text-white pt-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold">
          4ex.ninja
        </Link>
        <nav>
          <ul className="flex space-x-4">
            <li>
              <Link href="/">Home</Link>
            </li>
            <li>
              <Link href="/about">About</Link>
            </li>
            <li>
              <Link href="/feed">Feed</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
