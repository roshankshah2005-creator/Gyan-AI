import "./globals.css";
import { Analytics } from '@vercel/analytics/next';

export const metadata = {
  title: "GYAN - Intelligent Companion",
  description: "Multi-persona AI companion",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
