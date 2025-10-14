import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LiteLLM Admin Panel",
  description: "SaaS LiteLLM Administration Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
