type LoadingStateProps = {
  label: string;
  variant?: "page" | "inline";
  className?: string;
};

export default function LoadingState({ label, variant = "page", className = "" }: LoadingStateProps) {
  if (variant === "inline") {
    return (
      <div role="status" aria-live="polite" className={`flex items-center gap-2 text-sm text-[color:var(--theme-muted)] ${className}`}>
        <span aria-hidden="true" className="h-3 w-3 animate-spin rounded-full border-2 border-[color-mix(in_srgb,var(--theme-accent)_18%,transparent)] border-t-[var(--theme-accent)]" />
        <span>{label}</span>
      </div>
    );
  }

  return (
    <div role="status" aria-live="polite" className={`flex min-h-screen items-center justify-center bg-[color:var(--theme-bg)] ${className}`}>
      <div className="flex flex-col items-center gap-4">
        <span aria-hidden="true" className="h-12 w-12 animate-spin rounded-full border-2 border-[color-mix(in_srgb,var(--theme-accent)_18%,transparent)] border-t-[var(--theme-accent)]" />
        <span className="mono-label !text-[color:var(--theme-accent)]">{label}</span>
      </div>
    </div>
  );
}
