export function cn(...classes: Array<string | undefined | null | false>) {
  return classes.filter(Boolean).join(" ");
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong") {
  if (error instanceof TypeError && /fetch|network/i.test(error.message)) {
    return "Could not connect to Miryn. Check your connection and try again.";
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return fallback;
}
