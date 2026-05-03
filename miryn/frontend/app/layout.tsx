import type { Metadata } from "next";
import { Space_Grotesk, EB_Garamond, JetBrains_Mono } from "next/font/google";
import GoogleAuthProvider from "@/components/GoogleAuthProvider";
import "../styles/globals.css";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-space-grotesk",
});

const ebGaramond = EB_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  style: ["normal", "italic"],
  variable: "--font-eb-garamond",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Miryn AI | The Memory Layer",
  description: "A context-aware AI companion that remembers your patterns, beliefs, and evolution.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${ebGaramond.variable} ${jetBrainsMono.variable}`} suppressHydrationWarning>
      <body className="bg-void text-primary font-ui selection:bg-accent/30 selection:text-accent">
        <GoogleAuthProvider>
          {children}
        </GoogleAuthProvider>
      </body>
    </html>
  );
}
