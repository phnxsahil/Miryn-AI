"use client";

import { lazy, Suspense } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const HighlightedMarkdown = lazy(() => import("./HighlightedMarkdown"));

function PlainMarkdown({ content }: { content: string }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>;
}

export default function MarkdownBody({ content }: { content: string }) {
  if (!content.includes("```")) {
    return <PlainMarkdown content={content} />;
  }

  return (
    <Suspense fallback={<PlainMarkdown content={content} />}>
      <HighlightedMarkdown content={content} />
    </Suspense>
  );
}
