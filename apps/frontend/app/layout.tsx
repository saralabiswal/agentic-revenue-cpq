/**
 * Root Next.js layout and metadata for the command center application.
 *
 * @author Sarala Biswal
 */
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise AI Agent Platform",
  description: "Opportunity-to-quote copilot workspace",
  authors: [{ name: "Sarala Biswal" }],
};

/** Render the root HTML shell shared by every Next.js route. */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
