import { Suspense } from "react";
import ChatInterface from "@/components/Chat/ChatInterface";
import ErrorBoundary from "@/components/ErrorBoundary";

export default function ChatPage() {
  return (
    <ErrorBoundary>
      <Suspense fallback={null}>
        <ChatInterface />
      </Suspense>
    </ErrorBoundary>
  );
}
