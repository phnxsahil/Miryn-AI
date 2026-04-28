export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    try {
      await import("./sentry.server.config");
    } catch (error) {
      console.error("Failed to initialize Sentry server instrumentation", error);
    }
  }
}
