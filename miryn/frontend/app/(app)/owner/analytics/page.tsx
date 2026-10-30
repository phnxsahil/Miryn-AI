"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Metrics = {
  accounts_created: number; active_accounts: number; deleted_accounts: number;
  new_today: number; new_last_7_days: number; new_in_period: number;
  generated_at: string; timezone: string; notes: string[];
  daily_signups: { date: string; count: number }[];
};
export default function OwnerAnalytics() {
  const trafficConfigured = process.env.NEXT_PUBLIC_TRAFFIC_ANALYTICS_ENABLED === "true" && process.env.NEXT_PUBLIC_VERCEL_ENV === "production";
  const [data, setData] = useState<Metrics | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api.getOwnerAnalytics().then(result => { if (active) setData(result as Metrics); })
      .catch(err => { if (active) setError(err.message || "Analytics unavailable"); });
    return () => { active = false; };
  }, []);
  return <main className="mx-auto w-full max-w-5xl p-5 md:p-10 text-[color:var(--theme-text)]">
    <p className="mb-3 text-sm text-[color:var(--theme-dim)]">Miryn / Owner only</p>
    <h1 className="text-3xl mb-3">A clear view of your growth</h1>
    <p className="mb-8 text-[color:var(--theme-dim)]">Account counts from your database. No conversation content, email addresses or personal profiles appear here.</p>
    <section className="mb-8 rounded-2xl border border-[color:var(--theme-border)] p-5">
      <h2 className="text-xl mb-2">Website traffic</h2>
      <p className="mb-3 text-sm text-[color:var(--theme-dim)]">{trafficConfigured ? "Public-page traffic collection is configured for this production build. Confirm incoming events in the private Vercel dashboard; browser blockers can reduce counts." : "Traffic collection is disabled for this build."} Historical visits cannot be recovered. Anonymous visitors are not named people.</p>
      <a className="inline-flex min-h-11 items-center underline" href="https://vercel.com/shanu133s-projects/miryn-ai/analytics" target="_blank" rel="noopener noreferrer">Open private Vercel traffic dashboard</a>
    </section>
    {error ? <section role="alert" className="rounded-2xl border border-[color:var(--theme-border)] p-5"><h2 className="text-xl mb-2">Account metrics unavailable</h2><p>{error}</p><p className="mt-3 text-sm text-[color:var(--theme-dim)]">Access requires an authenticated account whose ID is in the server-only owner allowlist. No counts are public.</p></section> : !data ? <p role="status">Loading account counts...</p> : <>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">{[
        ["Accounts created", data.accounts_created], ["Not deleted", data.active_accounts],
        ["Marked deleted", data.deleted_accounts], ["New today (IST)", data.new_today],
        ["New in 7 IST days", data.new_last_7_days], ["New in 30 IST days", data.new_in_period],
      ].map(([label, value]) => <section key={label} className="rounded-2xl border border-[color:var(--theme-border)] p-5"><h2 className="text-sm text-[color:var(--theme-dim)] mb-3">{label}</h2><p className="text-3xl tabular-nums">{value}</p></section>)}</div>
      <h2 className="text-xl mb-4">Daily account creation</h2>
      <div className="rounded-2xl border border-[color:var(--theme-border)] overflow-hidden mb-6"><table className="w-full text-sm"><thead><tr><th className="text-left p-3">Date (IST)</th><th className="text-right p-3">New accounts</th></tr></thead><tbody>{[...data.daily_signups].reverse().map(row => <tr key={row.date} className="border-t border-[color:var(--theme-border)]"><td className="p-3">{row.date}</td><td className="p-3 text-right tabular-nums">{row.count}</td></tr>)}</tbody></table></div>
      <p className="text-sm mb-3 text-[color:var(--theme-dim)]">Updated {new Date(data.generated_at).toLocaleString()} (your device time).</p>
      <ul className="text-sm text-[color:var(--theme-dim)] space-y-2">{data.notes.map(note => <li key={note}>{note}</li>)}</ul>
    </>}
  </main>;
}
