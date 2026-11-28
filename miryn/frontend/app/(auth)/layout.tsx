import SwellBackground from "@/components/swell/SwellBackground";
import "@/styles/swell-assets.css";
import "@/styles/swell-tooth.css";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="swell-app relative min-h-[100dvh] bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] font-ui">
      <SwellBackground variant="empty" />
      {children}
    </div>
  );
}
