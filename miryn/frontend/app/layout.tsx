import type { Metadata } from "next";
import PostHogProvider from "@/components/PostHogProvider";
import { ThemeProvider } from "@/components/ThemeProvider";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "Miryn AI — Persistent Memory & Evolving AI Companion",
  description: "An AI companion that remembers, learns, and evolves with you. Powered by 3-tier memory architecture and dynamic identity engine.",
  icons: {
    icon: "/icon.png",
    shortcut: "/icon.png",
    apple: "/icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try { var theme = localStorage.getItem('miryn-theme'); document.documentElement.dataset.theme = theme === 'light' ? 'light' : 'dark'; } catch (_) { document.documentElement.dataset.theme = 'dark'; }`,
          }}
        />
      </head>
      <body className="bg-[#0a0a0a] text-[#f5f5f5] font-sans antialiased selection:bg-[#a8bb94] selection:text-[#0a0a0a]">
        <ThemeProvider>
          <PostHogProvider>{children}</PostHogProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
