import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CGL Official Record Book",
  description: "The official history, champions, standings and records of Charley's Gonna Lose fantasy football.",
  other: {
    "codex-preview": "development",
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
