import "./globals.css";

export const metadata = {
  title: "GYAN - Intelligent Companion",
  description: "Multi-persona AI companion",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
