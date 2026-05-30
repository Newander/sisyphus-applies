import type { Metadata } from "next";
import { FeatureMemoryButton } from "@/components/feature-memory-button";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Tracker",
  description: "Local dashboard for job search tracking",
  icons: {
    icon: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        {children}
        <FeatureMemoryButton />
      </body>
    </html>
  );
}
