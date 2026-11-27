import SwellBackground from "@/components/swell/SwellBackground";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="swell-app relative min-h-[100dvh] bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] font-ui">
      <SwellBackground variant="empty" />
      {children}
    </div>
  );
}
