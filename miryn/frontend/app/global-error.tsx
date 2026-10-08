"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-void text-white flex items-center justify-center px-6">
        <div className="max-w-md text-center space-y-4">
          <h2 className="text-3xl font-editorial font-light">Something broke.</h2>
          <p className="text-secondary text-sm">
            The error has been captured. Try again.
          </p>
          <button
            type="button"
            className="rounded-md bg-accent text-black px-5 py-3"
            onClick={reset}
          >
            Reload view
          </button>
        </div>
      </body>
    </html>
  );
}
