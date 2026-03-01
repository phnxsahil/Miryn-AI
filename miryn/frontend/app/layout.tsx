import type { Metadata } from "next";
import { Cormorant_Garamond, DM_Sans } from "next/font/google";
import GoogleAuthProvider from "@/components/GoogleAuthProvider";
import "../styles/globals.css";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-cormorant",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-dm",
});

export const metadata: Metadata = {
  title: "Miryn",
  description: "Context-aware AI companion with persistent memory",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const fontClass = `${cormorant.variable} ${dmSans.variable}`;
  return (
    <html lang="en" className={fontClass} suppressHydrationWarning>
      <body>
        <GoogleAuthProvider>
          {children}
        </GoogleAuthProvider>
      </body>
    </html>
  );
}
