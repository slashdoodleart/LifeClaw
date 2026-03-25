import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LifeClaw",
  description: "Hybrid AI Assistant for Terminal & Web",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
