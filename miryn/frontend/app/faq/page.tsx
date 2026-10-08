import Link from "next/link";

export const metadata = { title: "Questions about Miryn" };

const answers = [
  ["How does Miryn remember?", "Miryn saves useful context from conversations and retrieves relevant details in later chats."],
  ["Is my conversation private?", "Conversation content is encrypted in storage and handled according to the privacy policy."],
  ["Can I forget saved context?", "Yes. Review saved memories in Memory Bank and forget individual items whenever you want."],
  ["How do I get started?", "Create an account, open a conversation, and share what is on your mind."],
];

export default function FAQPage() {
  return <main className="landing-faq-page"><Link href="/">← Back to Miryn</Link><h1>Questions about Miryn</h1>{answers.map(([q, a]) => <section key={q}><h2>{q}</h2><p>{a}</p></section>)}<p><Link href="/privacy">Privacy policy</Link> · <Link href="/signup">Try Miryn</Link></p></main>;
}
