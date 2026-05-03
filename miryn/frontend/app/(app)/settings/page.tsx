"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session, User, NotificationPreferences } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";
import { Settings, Shield, Bell, Eye, Trash2, Key, Monitor, Activity, Check } from "lucide-react";

type NotificationToggleKey = "checkin_reminders" | "weekly_digest" | "browser_push";
type NotificationToggleItem = { id: NotificationToggleKey; label: string; desc: string };

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSaveSuccess] = useState<string | null>(null);

  // Form states
  const [passwordForm, setPasswordForm] = useState({
    current: "",
    new: "",
    confirm: "",
  });
  const [deleteConfirm, setDeleteConfirm] = useState("");
  const [textSize, setTextSize] = useState("base");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userData, sessionData] = await Promise.all([
          api.getMe(),
          api.getSessions(),
        ]);
        setUser(userData);
        setSessions(sessionData);
        
        const savedSize = localStorage.getItem("miryn_text_size") || "base";
        setTextSize(savedSize);
        applyTextSize(savedSize);
      } catch (err) {
        setError(getErrorMessage(err, "Failed to load settings"));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const applyTextSize = (size: string) => {
    const html = document.documentElement;
    html.classList.remove("text-sm", "text-base", "text-lg");
    html.classList.add(`text-${size}`);
    localStorage.setItem("miryn_text_size", size);
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new !== passwordForm.confirm) {
      setError("Passwords do not match");
      return;
    }
    try {
      setError(null);
      await api.updatePassword(passwordForm.current, passwordForm.new);
      setSaveSuccess("Password updated successfully");
      setPasswordForm({ current: "", new: "", confirm: "" });
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handlePrefChange = async (key: NotificationToggleKey, value: boolean) => {
    if (!user) return;
    const updatedPrefs = {
      ...user.notification_preferences,
      [key]: value,
      data_retention: user.data_retention
    };
    try {
      await api.updateNotificationPreferences(updatedPrefs);
      setUser({ ...user, notification_preferences: updatedPrefs });
      setSaveSuccess("Preferences updated");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleRetentionChange = async (value: string) => {
    if (!user) return;
    try {
      await api.updateNotificationPreferences({
        ...user.notification_preferences,
        data_retention: value
      });
      setUser({ ...user, data_retention: value });
      setSaveSuccess("Retention policy updated");
      setTimeout(() => setSaveSuccess(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== "DELETE") return;
    try {
      await api.deleteAccount();
      api.logout();
      router.push("/");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-t-2 border-[#c8b8ff] animate-spin" />
          <div className="mono-label !text-[#c8b8ff] animate-pulse">Retrieving Preferences...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#09090e] text-primary p-8 md:p-16 relative overflow-x-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/3 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-4xl mx-auto relative z-10 space-y-16 pb-32">
        <header className="space-y-6">
          <div className="flex items-center gap-3 mb-4">
            <Settings className="text-[#c8b8ff] w-6 h-6" />
            <span className="mono-label !text-[#3e3d54] font-bold uppercase tracking-[0.14em] text-[11px]">SYSTEM CONFIGURATION / 0XCF</span>
          </div>
          <h1 className="text-[38px] font-light tracking-tight mb-6 text-[#ede9ff]">Account <span className="editorial-italic text-[#c8b8ff]">Settings</span></h1>
          <p className="text-[#4a4868] text-[13px] max-w-2xl font-medium leading-relaxed">
            Adjust the resonance and privacy parameters of your digital identity.
          </p>
        </header>

        {error && (
          <div className="error-surface mb-8">
            <Shield size={18} />
            {error}
          </div>
        )}
        
        {success && (
          <div className="bg-[rgba(200,184,255,0.08)] border border-[rgba(200,184,255,0.2)] p-6 text-[#c8b8ff] text-sm mono-label flex items-center gap-4 rounded-[24px] font-medium shadow-sm">
            <Check size={18} className="text-[#c8b8ff]" />
            {success}
          </div>
        )}

        {/* Account Section */}
        <section className="space-y-8">
          <div className="flex items-center gap-4">
            <Key size={20} className="text-[#c8b8ff]" />
            <h2 className="mono-label font-bold uppercase tracking-[0.14em] text-[#7a7898] text-[11px]">Authentication</h2>
          </div>
          <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] rounded-[32px] p-10 space-y-10 shadow-sm" style={{ borderWidth: '0.5px' }}>
            <div className="space-y-3 pt-5">
              <label className="mono-label !text-[11px] font-bold uppercase tracking-[0.14em] text-[#7a7898]">Primary Identity</label>
              <div className="text-[#ede9ff] bg-[#0f0f17] border border-[rgba(255,255,255,0.08)] px-6 py-4 rounded-2xl text-[14px] font-normal" style={{ borderWidth: '0.5px' }}>
                {user?.email}
              </div>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-8 pt-5">
              <label className="mono-label !text-[11px] font-bold uppercase tracking-[0.14em] text-[#7a7898]">Security Credentials</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <input
                  type="password"
                  placeholder="Current password"
                  className="input-field"
                  value={passwordForm.current}
                  onChange={e => setPasswordForm({ ...passwordForm, current: e.target.value })}
                />
                <div className="grid grid-cols-1 gap-6">
                  <input
                    type="password"
                    placeholder="New password"
                    className="input-field"
                    value={passwordForm.new}
                    onChange={e => setPasswordForm({ ...passwordForm, new: e.target.value })}
                  />
                  <input
                    type="password"
                    placeholder="Confirm new password"
                    className="input-field"
                    value={passwordForm.confirm}
                    onChange={e => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                  />
                </div>
              </div>
              <button type="submit" className="h-14 px-10 bg-[#c8b8ff] text-[#09090e] rounded-full font-bold text-sm hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-accent/20">
                Update Credentials
              </button>
            </form>
          </div>
        </section>

        {/* Notifications */}
        <section className="space-y-8">
          <div className="flex items-center gap-4">
            <Bell size={20} className="text-[#c8b8ff]" />
            <h2 className="mono-label font-bold uppercase tracking-[0.14em] text-[#7a7898] text-[11px]">Resonance Channels</h2>
          </div>
          <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] rounded-[32px] p-10 space-y-6 shadow-sm" style={{ borderWidth: '0.5px' }}>
            {([
              { id: "checkin_reminders", label: "Check-in Protocol", desc: "Notification triggers for open-loop follow-ups." },
              { id: "weekly_digest", label: "Identity Summary", desc: "Weekly archival digest of your evolution." },
              { id: "browser_push", label: "Neural Interface", desc: "Real-time browser push notifications." }
            ] as NotificationToggleItem[]).map((item) => (
              <div key={item.id} className="flex items-center justify-between p-6 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
                <div>
                  <p className="text-[14px] font-normal text-[#ede9ff]">{item.label}</p>
                  <p className="text-[13px] text-[#4a4868] font-medium">{item.desc}</p>
                </div>
                <button
                  onClick={() => handlePrefChange(item.id, !user?.notification_preferences[item.id])}
                  className={`w-14 h-7 rounded-full transition-all relative ${user?.notification_preferences[item.id as keyof NotificationPreferences] ? "bg-[#c8b8ff] shadow-lg shadow-[rgba(200,184,255,0.2)]" : "bg-black/10"}`}
                >
                  <div className={`absolute top-1 w-5 h-5 bg-[#14141f] rounded-full transition-all shadow-sm ${user?.notification_preferences[item.id as keyof NotificationPreferences] ? "left-8" : "left-1"}`} />
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Appearance */}
        <section className="space-y-6">
          <div className="flex items-center gap-3">
            <Monitor size={16} className="text-[#c8b8ff]" />
            <h2 className="mono-label uppercase tracking-[0.14em] text-[#7a7898] text-[11px]">Visual Interface</h2>
          </div>
          <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] rounded-[32px] p-10 space-y-10 shadow-sm" style={{ borderWidth: '0.5px' }}>
            <div className="flex items-center justify-between p-6 rounded-2xl bg-white/[0.02] border border-white/[0.04]">
              <div>
                <p className="text-[14px] font-normal text-[#ede9ff]">Display Theme</p>
                <p className="text-[13px] text-[#4a4868] font-medium">Toggle between interface modalities.</p>
              </div>
              <div className="flex bg-black/5 p-1 rounded-xl border border-white/[0.04]">
                <button className="px-6 py-2 text-[11px] mono-label text-muted opacity-30 cursor-not-allowed font-bold">Void (Dark)</button>
                <button className="px-6 py-2 text-[11px] mono-label bg-[#c8b8ff] text-[#09090e] rounded-lg font-bold shadow-sm">Studio (Light)</button>
              </div>
            </div>

            <div className="space-y-6">
              <p className="text-[14px] font-normal text-[#ede9ff]">Text Calibration</p>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { id: "sm", label: "Compact" },
                  { id: "base", label: "Standard" },
                  { id: "lg", label: "Focused" }
                ].map(size => (
                  <button
                    key={size.id}
                    onClick={() => { setTextSize(size.id); applyTextSize(size.id); }}
                    className={`py-4 text-[11px] mono-label rounded-2xl border transition-all font-bold ${textSize === size.id ? "bg-[#c8b8ff] text-[#09090e] border-[#c8b8ff] shadow-lg shadow-[rgba(200,184,255,0.2)]" : "bg-[#14141f] border-white/[0.04] text-[#7a7898] hover:border-white/[0.08] shadow-sm"}`}
                  >
                    {size.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Privacy & Logs */}
        <section className="space-y-8">
          <div className="flex items-center gap-4">
            <Eye size={20} className="text-[#c8b8ff]" />
            <h2 className="mono-label font-bold uppercase tracking-[0.14em] text-[#7a7898] text-[11px]">Privacy & Session Metadata</h2>
          </div>
          <div className="space-y-6">
            <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] rounded-[32px] p-8 flex items-start gap-6 shadow-sm border-l-4 border-l-[#c8b8ff]" style={{ borderWidth: '0.5px' }}>
              <div className={`mt-1 p-4 rounded-2xl ${user?.encryption_enabled ? "bg-[rgba(200,184,255,0.12)] text-[#c8b8ff]" : "bg-red-500/10 text-red-400"}`}>
                <Shield size={24} />
              </div>
              <div>
                <p className="text-[14px] font-normal text-[#ede9ff]">Persistence Encryption</p>
                <p className="text-[13px] text-[#4a4868] mt-2 leading-relaxed font-medium">
                  {user?.encryption_enabled 
                    ? "All archival data is encrypted at rest using your unique cryptographic key. Miryn cannot access raw data without your active session." 
                    : "Caution: Active encryption is disabled for your profile."}
                </p>
              </div>
            </div>

            <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] rounded-[32px] p-10 shadow-sm" style={{ borderWidth: '0.5px' }}>
              <div className="flex items-center gap-4 mb-8">
                <Activity size={18} className="text-[#c8b8ff]" />
                <span className="mono-label !text-[11px] font-bold uppercase tracking-[0.14em] text-[#7a7898]">Active Session Log</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="mono-label !text-[10px] text-[#4a4868] opacity-50 border-b border-white/[0.04]">
                    <tr>
                      <th className="pb-4 font-bold uppercase tracking-widest">Network ID</th>
                      <th className="pb-4 font-bold uppercase tracking-widest">Last Interaction</th>
                    </tr>
                  </thead>
                  <tbody className="text-primary">
                    {sessions.map((s, i) => (
                      <tr key={i} className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02] transition-colors">
                        <td className="py-5 font-mono text-[12px] font-bold text-[#c8b8ff]">{s.ip}</td>
                        <td className="py-5 text-[12px] font-medium text-[#ede9ff]">{new Date(s.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Danger Zone */}
        <section className="space-y-8">
          <div className="flex items-center gap-4 text-[#e24b4a]">
            <Trash2 size={20} />
            <h2 className="mono-label font-bold uppercase tracking-[0.14em] text-[#e24b4a] text-[11px]">Terminal Deletion</h2>
          </div>
          <div className="bg-[rgba(226,75,74,0.06)] border border-[rgba(226,75,74,0.2)] rounded-[32px] p-10 space-y-10" style={{ borderWidth: '0.5px' }}>
            <p className="text-[15px] editorial-italic text-[#c17070] leading-relaxed">
              "To delete is to unmake. Once the matrix is dissolved, Miryn will no longer recognize your patterns, and the persistence layer will be permanently purged."
            </p>

            <div className="space-y-6">
              <p className="text-[11px] mono-label font-bold uppercase tracking-[0.14em] text-[#c17070]">Type <span className="text-[#e24b4a] font-bold">DELETE</span> to confirm purge</p>
              <input
                type="text"
                className="w-full bg-[rgba(226,75,74,0.08)] border border-[rgba(226,75,74,0.3)] px-6 py-4 rounded-2xl text-[14px] outline-none focus:border-[rgba(226,75,74,0.5)] transition-all text-[#e24b4a] placeholder:text-[rgba(226,75,74,0.3)] font-medium"
                placeholder="DELETE"
                value={deleteConfirm}
                onChange={e => setDeleteConfirm(e.target.value)}
              />
              <button
                disabled={deleteConfirm !== "DELETE"}
                onClick={handleDeleteAccount}
                className="w-full h-16 bg-[rgba(226,75,74,0.15)] text-[#e24b4a] rounded-2xl text-sm mono-label font-bold hover:bg-[rgba(226,75,74,0.2)] disabled:opacity-20 transition-all border border-[rgba(226,75,74,0.3)] uppercase tracking-widest"
              >
                Permanently Purge Identity Matrix
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
