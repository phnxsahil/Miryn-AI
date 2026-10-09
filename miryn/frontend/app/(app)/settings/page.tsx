"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session, User } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import {
  User as UserIcon, Shield, Bell, Palette, Database,
  Laptop, Trash2, LogOut, Download,
  AlertTriangle, CheckCircle2, Moon, Sun,
} from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

type SectionId = "profile" | "security" | "notifications" | "appearance" | "data";

const NAV: { id: SectionId; label: string; icon: React.ElementType }[] = [
  { id: "profile",       label: "Profile",       icon: UserIcon  },
  { id: "security",      label: "Security",       icon: Shield    },
  { id: "notifications", label: "Notifications",  icon: Bell      },
  { id: "appearance",    label: "Appearance",     icon: Palette   },
  { id: "data",          label: "Data & Privacy", icon: Database  },
];

function Row({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 border-b border-[color:var(--theme-border)] py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
      <div className="min-w-0">
        <p className="text-sm font-medium text-[color:var(--theme-text)]">{label}</p>
        {hint && <p className="text-xs text-[color:var(--theme-dim)] mt-0.5 leading-relaxed">{hint}</p>}
      </div>
      <div className="min-w-0 sm:shrink-0">{children}</div>
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      style={{ height: 22, width: 40 }}
      className={`relative rounded-full transition-colors duration-200 focus:outline-none ${checked ? "bg-[color:var(--theme-accent)]" : "bg-white/10"}`}
    >
      <span className={`absolute top-0.5 left-0.5 w-[18px] h-[18px] rounded-full bg-white shadow-sm transition-transform duration-200 ${checked ? "translate-x-[18px]" : "translate-x-0"}`} />
    </button>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [section, setSection] = useState<SectionId>("profile");
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; err?: boolean } | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [checkin, setCheckin] = useState(true);
  const [digest, setDigest] = useState(false);
  const [push, setPush] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [u, s] = await Promise.allSettled([api.getMe(), api.getSessions()]);
        if (u.status === "fulfilled") {
          setUser(u.value);
          setDisplayName(u.value.full_name || u.value.email?.split("@")[0] || "");
          const p = u.value.notification_preferences;
          if (p) {
            if (typeof p.checkin_reminders === "boolean") setCheckin(p.checkin_reminders);
            if (typeof p.weekly_digest === "boolean") setDigest(p.weekly_digest);
            if (typeof p.browser_push === "boolean") setPush(p.browser_push);
          }
        } else setLoadError(getErrorMessage(u.reason, "Could not load account details."));
        if (s.status === "fulfilled") setSessions(s.value);
      } finally { setLoading(false); }
    })();
  }, []);

  const showToast = (msg: string, err = false) => { setToast({ msg, err }); setTimeout(() => setToast(null), 3500); };

  const saveNotifications = async (key: string, value: boolean) => {
    if (!user) return;
    try {
      const prefs = { ...user.notification_preferences, [key]: value };
      await api.updateNotificationPreferences(prefs);
      setUser({ ...user, notification_preferences: prefs });
    } catch (error) {
      if (key === "checkin_reminders") setCheckin(!value);
      if (key === "weekly_digest") setDigest(!value);
      if (key === "browser_push") setPush(!value);
      showToast(getErrorMessage(error, "Could not save notification preference."), true);
    }
  };

  const initials = (displayName || user?.email || "U").slice(0, 2).toUpperCase();

  if (loading) return <div className="flex items-center justify-center h-full text-[color:var(--theme-dim)] text-sm">Loading settings…</div>;

  return (
    <div className="flex min-h-full flex-col bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] relative md:flex-row">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2.5 px-4 py-3 rounded-2xl text-sm font-medium shadow-xl animate-in slide-in-from-top-2 duration-200 border ${toast.err ? "border-red-500/25 text-red-400 bg-[color:var(--theme-card)]" : "border-[color:var(--theme-accent)]/25 text-[color:var(--theme-accent)] bg-[color:var(--theme-card)]"}`}>
          {toast.err ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
          {toast.msg}
        </div>
      )}

      {/* Sidebar */}
      <aside className="settings-nav flex w-full shrink-0 gap-1 overflow-x-auto border-b border-[color:var(--theme-border)] px-3 py-3 md:w-48 md:flex-col md:overflow-visible md:border-b-0 md:py-8">
        <p className="hidden px-3 mb-3 text-[10.5px] font-mono uppercase tracking-widest text-[color:var(--theme-dim)] md:block">Account</p>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setSection(id)} className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm transition-colors md:w-full ${section === id ? "bg-[color:var(--theme-overlay)] text-[color:var(--theme-text)]" : "text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)] hover:bg-[color:var(--theme-overlay)]"}`}>
            <Icon size={15} className={section === id ? "text-[color:var(--theme-accent)]" : ""} />
            {label}
          </button>
        ))}
        <div className="mt-auto hidden pt-4 border-t border-[color:var(--theme-border)] md:block">
          <button onClick={() => { api.logout(); router.push("/"); }} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-[color:var(--theme-dim)] hover:text-red-400 hover:bg-red-500/[0.06] transition-all w-full">
            <LogOut size={15} />Sign out
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="w-full min-w-0 flex-1 px-5 py-8 md:max-w-2xl md:px-8 md:py-12">
        {loadError && <div role="alert" className="mb-6 rounded-xl bg-[color:var(--theme-danger-bg)] p-4 text-sm text-[color:var(--theme-danger-text)]">{loadError} <button type="button" onClick={() => window.location.reload()} className="ml-2 underline">Try again</button></div>}

        {section === "profile" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h1 className="font-editorial text-3xl md:text-4xl">Profile</h1><p className="mt-2 text-sm text-[color:var(--theme-muted)]">Your account details</p></div>
            <div className="flex items-center gap-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--theme-card)] text-sm font-semibold text-[color:var(--theme-accent)]">{initials}</div>
              <div>
                <p className="text-sm font-medium">{displayName || "Your Name"}</p>
                <p className="text-xs text-[color:var(--theme-dim)] mt-0.5">{user?.email}</p>
              </div>
            </div>
            <div className="bg-[color:var(--theme-card)] rounded-2xl border border-[color:var(--theme-border)] px-5 divide-y divide-white/[0.04]">
              <Row label="Name" hint="Profile name is currently read-only."><span className="text-sm text-[color:var(--theme-muted)]">{displayName || "Not set"}</span></Row>
              <Row label="Email"><span className="text-sm text-[color:var(--theme-dim)]">{user?.email}</span></Row>
            </div>
          </div>
        )}

        {section === "security" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h1 className="font-editorial text-3xl md:text-4xl">Security</h1><p className="mt-2 text-sm text-[color:var(--theme-muted)]">Password and active sessions</p></div>
            <div className="bg-[color:var(--theme-card)] rounded-2xl border border-[color:var(--theme-border)] p-5 space-y-3">
              <h3 className="text-sm font-semibold text-[color:var(--theme-muted)]">Change password</h3>
              <form onSubmit={async e => { e.preventDefault(); if (pwForm.next !== pwForm.confirm) return showToast("Passwords don't match", true); try { await api.updatePassword(pwForm.current, pwForm.next); setPwForm({ current: "", next: "", confirm: "" }); showToast("Password updated"); } catch (err) { showToast(getErrorMessage(err), true); }}} className="space-y-2.5">
                {([["current","Current password"],["next","New password"],["confirm","Confirm new password"]] as const).map(([k, ph]) => (
                  <input key={k} type="password" placeholder={ph} value={pwForm[k]} onChange={e => setPwForm(p => ({...p,[k]:e.target.value}))} className="w-full bg-[color:var(--theme-input)] border border-[color:var(--theme-border)] rounded-xl px-4 py-2.5 text-sm text-[color:var(--theme-text)] outline-none focus:border-[color:var(--theme-accent)]/40 placeholder:text-[color:var(--theme-dim)]" />
                ))}
                <button type="submit" className="px-5 py-2 bg-[color:var(--theme-accent)] hover:bg-[color:var(--theme-accent-strong)] text-[color:var(--theme-accent-contrast)] font-semibold text-sm rounded-xl transition-colors">Update</button>
              </form>
            </div>
            <div className="space-y-2.5">
              <h3 className="text-sm font-semibold text-[color:var(--theme-muted)]">Active sessions</h3>
              {sessions.length === 0 ? <p className="text-sm text-[color:var(--theme-dim)]">No sessions found.</p> : sessions.map((s, index) => (
                <div key={`${s.timestamp}-${s.ip ?? "unknown"}-${index}`} className="flex items-center gap-3 bg-[color:var(--theme-card)] border border-[color:var(--theme-border)] rounded-2xl px-4 py-3">
                  <Laptop size={15} className="text-[color:var(--theme-dim)] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="flex items-center gap-2 text-sm text-[color:var(--theme-text)] truncate">{s.device ?? "Unknown device"}{index === 0 && <span className="rounded-full bg-[color:var(--theme-accent)]/10 px-1.5 py-0.5 text-[10px] font-medium text-[color:var(--theme-accent)]">This device</span>}</p>
                    <p className="text-xs text-[color:var(--theme-dim)] mt-0.5">{s.ip ?? "IP not recorded"} · {s.timestamp ? new Date(s.timestamp).toLocaleString() : ""}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="bg-[color-mix(in_srgb,var(--theme-accent)_12%,var(--theme-card))] border border-[color:var(--theme-accent)]/20 rounded-2xl px-4 py-3.5 flex items-center gap-3">
              <Shield size={15} className="text-[color:var(--theme-accent)] shrink-0" />
              <div><p className="text-sm font-medium text-[color:var(--theme-accent)]">Fernet encryption active</p><p className="text-xs text-[color:var(--theme-dim)] mt-0.5">All messages encrypted at rest.</p></div>
            </div>
          </div>
        )}

        {section === "notifications" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h1 className="font-editorial text-3xl md:text-4xl">Notifications</h1><p className="mt-2 text-sm text-[color:var(--theme-muted)]">Choose what Miryn notifies you about</p></div>
            <div className="bg-[color:var(--theme-card)] rounded-2xl border border-[color:var(--theme-border)] px-5 divide-y divide-white/[0.04]">
              <Row label="Daily check-in" hint="Gentle prompts to reflect and reconnect"><Toggle checked={checkin} onChange={v => { setCheckin(v); void saveNotifications("checkin_reminders", v); }} /></Row>
              <Row label="Weekly digest" hint="Summary of your emotional patterns and memories"><Toggle checked={digest} onChange={v => { setDigest(v); void saveNotifications("weekly_digest", v); }} /></Row>
              <Row label="Browser push" hint="Requires browser permission"><Toggle checked={push} onChange={v => { setPush(v); void saveNotifications("browser_push", v); }} /></Row>
            </div>
          </div>
        )}

        {section === "appearance" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h1 className="font-editorial text-3xl md:text-4xl">Appearance</h1><p className="mt-2 text-sm text-[color:var(--theme-muted)]">Choose a comfortable theme</p></div>
            <div className="bg-[color:var(--theme-card)] rounded-2xl border border-[color:var(--theme-border)] px-5 divide-y divide-white/[0.04]">
              <Row label="Theme" hint="Dark or light interface">
                <div className="flex gap-2">
                  {(["dark","light"] as const).map(t => (
                    <button key={t} onClick={() => setTheme(t)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${theme === t ? "bg-[color:var(--theme-accent)]/10 border-[color:var(--theme-accent)]/25 text-[color:var(--theme-accent)]" : "border-[color:var(--theme-border)] text-[color:var(--theme-dim)] hover:text-[color:var(--theme-muted)]"}`}>
                      {t === "dark" ? <Moon size={12} /> : <Sun size={12} />}
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </Row>
            </div>
          </div>
        )}

        {section === "data" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h1 className="font-editorial text-3xl md:text-4xl">Data & privacy</h1><p className="mt-2 text-sm text-[color:var(--theme-muted)]">Export or remove your data</p></div>
            <div className="bg-[color:var(--theme-card)] rounded-2xl border border-[color:var(--theme-border)] px-5 divide-y divide-white/[0.04]">
              <Row label="Episodic retention" hint="Current retention setting"><span className="text-sm text-[color:var(--theme-muted)]">{user?.data_retention || "7d"}</span></Row>
              <Row label="Export data" hint="Download all memories, identity, and conversations as JSON">
                <button onClick={async () => { setExporting(true); try { const blob = await api.exportData(); const a = Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:`miryn-export-${new Date().toISOString().slice(0,10)}.json`}); document.body.appendChild(a); a.click(); a.remove(); showToast("Export downloaded"); } catch(err){showToast(getErrorMessage(err,"Export failed"),true);} finally{setExporting(false);}}} disabled={exporting} className="flex items-center gap-2 px-4 py-2 text-sm bg-[color:var(--theme-input)] border border-[color:var(--theme-border)] rounded-xl text-[color:var(--theme-text)] hover:bg-[color:var(--theme-card-hover)] transition-colors disabled:opacity-50">
                  <Download size={13} />{exporting ? "Exporting..." : "Export"}
                </button>
              </Row>
              <Row label="Purge episodic memory" hint="Delete short-term memories, keep Core Identity">
                <button onClick={async () => { try { await api.purgeEpisodicMemory(); showToast("Episodic memories purged"); } catch(err){showToast(getErrorMessage(err),true);}}} className="flex items-center gap-2 px-4 py-2 text-sm text-orange-400 bg-orange-500/[0.06] border border-orange-500/15 rounded-xl hover:bg-orange-500/10 transition-colors">
                  <Trash2 size={13} />Purge
                </button>
              </Row>
              <Row label="Clear conversations" hint="Permanently remove all chat history">
                <button onClick={async () => { try { await api.clearConversations(); showToast("Conversations cleared"); } catch(err){showToast(getErrorMessage(err),true);}}} className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 bg-red-500/[0.06] border border-red-500/15 rounded-xl hover:bg-red-500/10 transition-colors">
                  <Trash2 size={13} />Clear
                </button>
              </Row>
            </div>
            <div className="bg-[color:var(--theme-danger-bg)] border border-[color:var(--theme-danger-border)] rounded-2xl p-5 space-y-4">
              <div className="flex items-center gap-2 text-red-400"><AlertTriangle size={15} /><h3 className="text-sm font-semibold">Delete account</h3></div>
              <p className="text-xs text-[color:var(--theme-dim)] leading-relaxed">Permanently deletes your account, memories, and all data. Cannot be undone.</p>
              <div className="flex items-center gap-2.5">
                <input value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)} placeholder='Type "DELETE" to confirm' className="flex-1 bg-[color:var(--theme-input)] border border-red-500/15 rounded-xl px-3 py-2 text-sm text-[color:var(--theme-text)] outline-none focus:border-red-500/30 placeholder:text-[color:var(--theme-dim)]" />
                <button onClick={async () => { if(deleteConfirm!=="DELETE") return showToast('Type DELETE to confirm',true); try{await api.deleteAccount();api.logout();router.push("/");}catch(err){showToast(getErrorMessage(err),true);}}} disabled={deleteConfirm !== "DELETE"} className="px-4 py-2 text-sm text-red-400 bg-red-500/[0.08] border border-red-500/20 rounded-xl hover:bg-red-500/12 transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

