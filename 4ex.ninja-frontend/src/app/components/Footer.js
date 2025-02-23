export default function Footer() {
  const currentYear = new Date().getFullYear();
  return (
    <footer className="bg-black p-4 ">
      <div className="container mx-auto text-center">
        <p>
          &copy; {currentYear} Made by a Ninja. Trade at your own risk.
        </p>
      </div>
    </footer>
  );
}
