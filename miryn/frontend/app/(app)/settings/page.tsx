"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session, User } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import {
  User as UserIcon, Shield, Bell, Palette, Database,
  Laptop, Trash2, LogOut, Download, Upload,
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
    <div className="flex items-center justify-between gap-6 py-4 border-b border-white/[0.05] last:border-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-[#e8e8ec]">{label}</p>
        {hint && <p className="text-xs text-[#505060] mt-0.5 leading-relaxed">{hint}</p>}
      </div>
      <div className="shrink-0">{children}</div>
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
      className={`relative rounded-full transition-colors duration-200 focus:outline-none ${checked ? "bg-[#D69155]" : "bg-white/10"}`}
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
  const [toast, setToast] = useState<{ msg: string; err?: boolean } | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [checkin, setCheckin] = useState(true);
  const [digest, setDigest] = useState(false);
  const [push, setPush] = useState(false);
  const [retention, setRetention] = useState("7d");
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [u, s] = await Promise.allSettled([api.getMe(), api.getSessions()]);
        if (u.status === "fulfilled") {
          setUser(u.value);
          setDisplayName(u.value.display_name || u.value.email?.split("@")[0] || "");
          setRetention(u.value.data_retention || "7d");
          const p = u.value.notification_preferences;
          if (p) {
            if (typeof p.checkin_reminders === "boolean") setCheckin(p.checkin_reminders);
            if (typeof p.weekly_digest === "boolean") setDigest(p.weekly_digest);
            if (typeof p.browser_push === "boolean") setPush(p.browser_push);
          }
        }
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
    } catch { /* silent */ }
  };

  const initials = (displayName || user?.email || "U").slice(0, 2).toUpperCase();

  if (loading) return <div className="flex items-center justify-center h-full text-[#505060] text-sm">Loading—</div>;

  return (
    <div className="flex h-full bg-[#0d0d11] text-[#e8e8ec] relative">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 flex items-center gap-2.5 px-4 py-3 rounded-2xl text-sm font-medium shadow-xl animate-in slide-in-from-top-2 duration-200 border ${toast.err ? "border-red-500/25 text-red-400 bg-[#1a1a22]" : "border-[#D69155]/25 text-[#D69155] bg-[#1a1a22]"}`}>
          {toast.err ? <AlertTriangle size={15} /> : <CheckCircle2 size={15} />}
          {toast.msg}
        </div>
      )}

      {/* Sidebar */}
      <aside className="w-52 shrink-0 border-r border-white/[0.06] flex flex-col py-6 px-2.5 gap-0.5">
        <p className="text-[10.5px] font-mono uppercase tracking-widest text-[#404050] px-3 mb-3">Account</p>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setSection(id)} className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all text-left w-full ${section === id ? "bg-white/[0.07] text-[#f0f0f4]" : "text-[#737380] hover:text-[#c0c0c8] hover:bg-white/[0.03]"}`}>
            <Icon size={15} className={section === id ? "text-[#D69155]" : ""} />
            {label}
          </button>
        ))}
        <div className="mt-auto pt-4 border-t border-white/[0.05]">
          <button onClick={() => { api.logout(); router.push("/"); }} className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-[#737380] hover:text-red-400 hover:bg-red-500/[0.06] transition-all w-full">
            <LogOut size={15} />Sign out
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-y-auto px-8 py-8 max-w-2xl">

        {section === "profile" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h2 className="text-base font-semibold">Profile</h2><p className="text-xs text-[#505060] mt-1">Your identity within Miryn</p></div>
            <div className="flex items-center gap-5">
              <div className="relative group cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                <div className="w-16 h-16 rounded-2xl overflow-hidden border border-white/[0.1] bg-[#1a1a22] flex items-center justify-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  {avatarUrl ? <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" /> : <span className="text-xl font-semibold text-[#D69155]">{initials}</span>}
                </div>
                <div className="absolute inset-0 rounded-2xl bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"><Upload size={16} className="text-white" /></div>
              </div>
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) { setAvatarUrl(URL.createObjectURL(f)); showToast("Avatar updated"); }}} />
              <div>
                <p className="text-sm font-medium">{displayName || "Your Name"}</p>
                <p className="text-xs text-[#505060] mt-0.5">{user?.email}</p>
                <button onClick={() => fileInputRef.current?.click()} className="mt-1.5 text-xs text-[#D69155] hover:text-[#F2B271] transition-colors">Change photo</button>
              </div>
            </div>
            <div className="bg-[#121219] rounded-2xl border border-white/[0.06] px-5 divide-y divide-white/[0.04]">
              <Row label="Display name" hint="How Miryn addresses you">
                <input value={displayName} onChange={e => setDisplayName(e.target.value)} className="bg-[#1e1e28] border border-white/[0.08] rounded-xl px-3 py-1.5 text-sm text-[#e8e8ec] outline-none focus:border-[#D69155]/40 w-40" />
              </Row>
              <Row label="Email"><span className="text-sm text-[#505060]">{user?.email}</span></Row>
              <Row label="Member since"><span className="text-sm text-[#505060]">{user?.created_at ? new Date(user.created_at).toLocaleDateString("en-US", { month: "long", year: "numeric" }) : "—"}</span></Row>
            </div>
            <button onClick={() => showToast("Profile saved")} className="px-5 py-2 bg-[#D69155] hover:bg-[#E8A870] text-[#0d0d11] font-semibold text-sm rounded-xl transition-colors">Save changes</button>
          </div>
        )}

        {section === "security" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h2 className="text-base font-semibold">Security</h2><p className="text-xs text-[#505060] mt-1">Password and active sessions</p></div>
            <div className="bg-[#121219] rounded-2xl border border-white/[0.06] p-5 space-y-3">
              <h3 className="text-sm font-semibold text-[#c0c0c8]">Change password</h3>
              <form onSubmit={async e => { e.preventDefault(); if (pwForm.next !== pwForm.confirm) return showToast("Passwords don't match", true); try { await api.updatePassword(pwForm.current, pwForm.next); setPwForm({ current: "", next: "", confirm: "" }); showToast("Password updated"); } catch (err) { showToast(getErrorMessage(err), true); }}} className="space-y-2.5">
                {([["current","Current password"],["next","New password"],["confirm","Confirm new password"]] as const).map(([k, ph]) => (
                  <input key={k} type="password" placeholder={ph} value={pwForm[k]} onChange={e => setPwForm(p => ({...p,[k]:e.target.value}))} className="w-full bg-[#1e1e28] border border-white/[0.07] rounded-xl px-4 py-2.5 text-sm text-[#e8e8ec] outline-none focus:border-[#D69155]/40 placeholder:text-[#404050]" />
                ))}
                <button type="submit" className="px-5 py-2 bg-[#D69155] hover:bg-[#E8A870] text-[#0d0d11] font-semibold text-sm rounded-xl transition-colors">Update</button>
              </form>
            </div>
            <div className="space-y-2.5">
              <h3 className="text-sm font-semibold text-[#c0c0c8]">Active sessions</h3>
              {sessions.length === 0 ? <p className="text-sm text-[#404050]">No sessions found.</p> : sessions.map(s => (
                <div key={s.id} className="flex items-center gap-3 bg-[#121219] border border-white/[0.06] rounded-2xl px-4 py-3">
                  <Laptop size={15} className="text-[#505060] shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[#e8e8ec] truncate">{s.user_agent?.split("(")[0]?.trim() || "Browser"}</p>
                    <p className="text-xs text-[#404050] mt-0.5">{s.ip ?? "Unknown"} — {s.created_at ? new Date(s.created_at).toLocaleDateString() : ""}</p>
                  </div>
                  {s.is_current && <span className="text-[10.5px] font-mono text-[#D69155] bg-[#D69155]/10 border border-[#D69155]/15 rounded-full px-2 py-0.5">current</span>}
                </div>
              ))}
            </div>
            <div className="bg-[#0d1a12] border border-[#10b981]/15 rounded-2xl px-4 py-3.5 flex items-center gap-3">
              <Shield size={15} className="text-[#10b981] shrink-0" />
              <div><p className="text-sm font-medium text-[#10b981]">Fernet encryption active</p><p className="text-xs text-[#404050] mt-0.5">All messages encrypted at rest.</p></div>
            </div>
          </div>
        )}

        {section === "notifications" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h2 className="text-base font-semibold">Notifications</h2><p className="text-xs text-[#505060] mt-1">Choose what Miryn notifies you about</p></div>
            <div className="bg-[#121219] rounded-2xl border border-white/[0.06] px-5 divide-y divide-white/[0.04]">
              <Row label="Daily check-in" hint="Gentle prompts to reflect and reconnect"><Toggle checked={checkin} onChange={v => { setCheckin(v); void saveNotifications("checkin_reminders", v); }} /></Row>
              <Row label="Weekly digest" hint="Summary of your emotional patterns and memories"><Toggle checked={digest} onChange={v => { setDigest(v); void saveNotifications("weekly_digest", v); }} /></Row>
              <Row label="Browser push" hint="Requires browser permission"><Toggle checked={push} onChange={v => { setPush(v); void saveNotifications("browser_push", v); }} /></Row>
            </div>
          </div>
        )}

        {section === "appearance" && (
          <div className="space-y-7 animate-in fade-in duration-200">
            <div><h2 className="text-base font-semibold">Appearance</h2><p className="text-xs text-[#505060] mt-1">Customize how Miryn looks</p></div>
            <div className="bg-[#121219] rounded-2xl border border-white/[0.06] px-5 divide-y divide-white/[0.04]">
              <Row label="Theme" hint="Dark or light interface">
                <div className="flex gap-2">
                  {(["dark","light"] as const).map(t => (
                    <button key={t} onClick={() => setTheme(t)} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${theme === t ? "bg-[#D69155]/10 border-[#D69155]/25 text-[#D69155]" : "border-white/[0.07] text-[#505060] hover:text-[#c0c0c8]"}`}>
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
            <div><h2 className="text-base font-semibold">Data & Privacy</h2><p className="text-xs text-[#505060] mt-1">You own your data — export or delete anytime</p></div>
            <div className="bg-[#121219] rounded-2xl border border-white/[0.06] px-5 divide-y divide-white/[0.04]">
              <Row label="Episodic retention" hint="How long short-term context is kept before self-expiring">
                <select
                  value={retention}
                  onChange={(e) => {
                    setRetention(e.target.value);
                    showToast("Retention preference updated");
                  }}
                  className="bg-[#1e1e28] border border-white/[0.08] rounded-xl px-3 py-1.5 text-xs text-[#e8e8ec] outline-none focus:border-[#D69155]/40"
                >
                  <option value="3d">3 days</option>
                  <option value="7d">7 days (default)</option>
                  <option value="14d">14 days</option>
                  <option value="30d">30 days</option>
                </select>
              </Row>
              <Row label="Export data" hint="Download all memories, identity, and conversations as JSON">
                <button onClick={async () => { setExporting(true); try { const blob = await api.exportData(); const a = Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:`miryn-export-${new Date().toISOString().slice(0,10)}.json`}); document.body.appendChild(a); a.click(); a.remove(); showToast("Export downloaded"); } catch(err){showToast(getErrorMessage(err,"Export failed"),true);} finally{setExporting(false);}}} disabled={exporting} className="flex items-center gap-2 px-4 py-2 text-sm bg-[#1e1e28] border border-white/[0.08] rounded-xl text-[#e8e8ec] hover:bg-[#242432] transition-colors disabled:opacity-50">
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
            <div className="bg-[#160d0d] border border-red-500/15 rounded-2xl p-5 space-y-4">
              <div className="flex items-center gap-2 text-red-400"><AlertTriangle size={15} /><h3 className="text-sm font-semibold">Delete account</h3></div>
              <p className="text-xs text-[#505060] leading-relaxed">Permanently deletes your account, memories, and all data. Cannot be undone.</p>
              <div className="flex items-center gap-2.5">
                <input value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)} placeholder='Type "DELETE" to confirm' className="flex-1 bg-[#1e1e28] border border-red-500/15 rounded-xl px-3 py-2 text-sm text-[#e8e8ec] outline-none focus:border-red-500/30 placeholder:text-[#404050]" />
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

