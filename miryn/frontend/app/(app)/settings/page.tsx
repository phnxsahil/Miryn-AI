"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Session, User, NotificationPreferences } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

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
        
        // Load text size
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

  if (loading) return <div className="p-8 text-secondary">Loading settings...</div>;

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-10 space-y-12 pb-24">
      <header>
        <h1 className="text-3xl font-serif font-light mb-2">Settings</h1>
        <p className="text-secondary text-sm">Manage your account, privacy, and interface preferences.</p>
      </header>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl">
          {error}
        </div>
      )}
      {success && (
        <div className="p-4 bg-green-500/10 border border-green-500/20 text-green-400 text-sm rounded-xl">
          {success}
        </div>
      )}

      {/* 1. ACCOUNT */}
      <section className="space-y-6">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-secondary font-bold">Account</h2>
        <div className="bg-surface border border-white/10 rounded-2xl p-6 space-y-8">
          <div>
            <label className="block text-xs text-secondary mb-2 uppercase tracking-wider">Email Address</label>
            <div className="text-white bg-white/5 border border-white/5 px-4 py-2.5 rounded-full text-sm">
              {user?.email}
            </div>
          </div>

          <form onSubmit={handlePasswordChange} className="space-y-4">
            <label className="block text-xs text-secondary mb-2 uppercase tracking-wider">Change Password</label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input
                type="password"
                placeholder="Current password"
                className="bg-white/5 border border-white/10 px-4 py-2.5 rounded-full text-sm focus:border-accent-purple/50 outline-none"
                value={passwordForm.current}
                onChange={e => setPasswordForm({ ...passwordForm, current: e.target.value })}
              />
              <input
                type="password"
                placeholder="New password"
                className="bg-white/5 border border-white/10 px-4 py-2.5 rounded-full text-sm focus:border-accent-purple/50 outline-none"
                value={passwordForm.new}
                onChange={e => setPasswordForm({ ...passwordForm, new: e.target.value })}
              />
              <input
                type="password"
                placeholder="Confirm new password"
                className="bg-white/5 border border-white/10 px-4 py-2.5 rounded-full text-sm focus:border-accent-purple/50 outline-none"
                value={passwordForm.confirm}
                onChange={e => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
              />
            </div>
            <button
              type="submit"
              className="mt-2 text-xs text-accent-purple hover:underline"
            >
              Update Password
            </button>
          </form>

          <div className="pt-4 border-t border-white/5">
            <label className="block text-xs text-secondary mb-3 uppercase tracking-wider">Connected Accounts</label>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs">G</div>
              <span className="text-sm">Google</span>
              <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full ${user?.has_password ? "bg-white/5 text-secondary" : "bg-accent-purple/20 text-accent-purple"}`}>
                {user?.has_password ? "Optional Login" : "Primary Login"}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. NOTIFICATIONS */}
      <section className="space-y-6">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-secondary font-bold">Notifications</h2>
        <div className="bg-surface border border-white/10 rounded-2xl p-6 space-y-6">
          {([
            { id: "checkin_reminders", label: "Check-in reminders", desc: "Get notified when Miryn wants to follow up on an open loop." },
            { id: "weekly_digest", label: "Weekly digest email", desc: "A summary of your identity evolution and key patterns." },
            { id: "browser_push", label: "Browser push notifications", desc: "Receive instant updates in your browser." }
          ] as NotificationToggleItem[]).map((item) => (
            <div key={item.id} className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white">{item.label}</p>
                <p className="text-xs text-secondary">{item.desc}</p>
              </div>
              <button
                onClick={() => handlePrefChange(item.id, !user?.notification_preferences[item.id])}
                className={`w-10 h-5 rounded-full transition-colors relative ${user?.notification_preferences[item.id as keyof NotificationPreferences] ? "bg-accent-purple" : "bg-white/10"}`}
              >
                <div className={`absolute top-1 w-3 h-3 bg-white rounded-full transition-all ${user?.notification_preferences[item.id as keyof NotificationPreferences] ? "left-6" : "left-1"}`} />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* 3. PRIVACY */}
      <section className="space-y-6">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-secondary font-bold">Privacy</h2>
        <div className="space-y-4">
          <div className="bg-surface border border-white/10 rounded-2xl p-6 flex items-start space-x-4">
            <div className={`mt-1 p-2 rounded-lg ${user?.encryption_enabled ? "bg-green-500/10 text-green-400" : "bg-amber-500/10 text-amber-400"}`}>
              🛡️
            </div>
            <div>
              <p className="text-sm text-white">Memory Encryption</p>
              <p className="text-xs text-secondary mt-1">
                {user?.encryption_enabled 
                  ? "All Tier-2 and Tier-3 memories are encrypted at rest using your unique server key." 
                  : "Memory encryption is currently disabled on the server."}
              </p>
            </div>
          </div>

          <div className="bg-surface border border-white/10 rounded-2xl p-6">
            <label className="block text-xs text-secondary mb-4 uppercase tracking-wider">Data Retention</label>
            <select
              value={user?.data_retention}
              onChange={e => handleRetentionChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 px-4 py-2.5 rounded-full text-sm outline-none focus:border-accent-purple/50"
            >
              <option value="forever">Forever</option>
              <option value="1year">1 Year</option>
              <option value="6months">6 Months</option>
              <option value="3months">3 Months</option>
            </select>
          </div>

          <div className="bg-surface border border-white/10 rounded-2xl p-6">
            <label className="block text-xs text-secondary mb-4 uppercase tracking-wider">Recent Session Log</label>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="text-secondary uppercase tracking-tighter border-b border-white/5">
                  <tr>
                    <th className="pb-2 font-medium">IP Address</th>
                    <th className="pb-2 font-medium">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="text-white">
                  {sessions.map((s, i) => (
                    <tr key={i} className="border-b border-white/5 last:border-0">
                      <td className="py-3 font-mono">{s.ip}</td>
                      <td className="py-3">{new Date(s.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* 4. APPEARANCE */}
      <section className="space-y-6">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-secondary font-bold">Appearance</h2>
        <div className="bg-surface border border-white/10 rounded-2xl p-6 space-y-8">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-white">Theme</p>
              <p className="text-xs text-secondary">Switch between dark and light modes.</p>
            </div>
            <div className="flex bg-white/5 p-1 rounded-full border border-white/5">
              <button className="px-4 py-1.5 text-xs bg-accent-purple text-void rounded-full">Dark</button>
              <button className="px-4 py-1.5 text-xs text-secondary opacity-50 cursor-not-allowed">Light (Soon)</button>
            </div>
          </div>

          <div>
            <p className="text-sm text-white mb-4">Text Size</p>
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "sm", label: "Compact" },
                { id: "base", label: "Default" },
                { id: "lg", label: "Comfortable" }
              ].map(size => (
                <button
                  key={size.id}
                  onClick={() => { setTextSize(size.id); applyTextSize(size.id); }}
                  className={`py-2 text-xs rounded-xl border transition-all ${textSize === size.id ? "bg-accent-purple/10 border-accent-purple text-accent-purple" : "bg-white/5 border-white/5 text-secondary hover:bg-white/10"}`}
                >
                  {size.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 5. DANGER ZONE */}
      <section className="space-y-6">
        <h2 className="text-[10px] uppercase tracking-[0.2em] text-red-400 font-bold">Danger Zone</h2>
        <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6 space-y-6">
          <div>
            <h3 className="text-white text-sm font-medium">Delete your account</h3>
            <p className="text-xs text-secondary mt-1 leading-relaxed">
              Once you delete your account, there is no going back. All of your memories, identity profile, and conversations will be permanently erased from our primary database.
            </p>
          </div>

          <div className="space-y-3">
            <p className="text-[10px] text-secondary uppercase tracking-widest">Type <span className="text-white font-mono">DELETE</span> to confirm</p>
            <input
              type="text"
              className="w-full bg-red-500/5 border border-red-500/20 px-4 py-2.5 rounded-full text-sm outline-none focus:border-red-500/50 text-white"
              placeholder="DELETE"
              value={deleteConfirm}
              onChange={e => setDeleteConfirm(e.target.value)}
            />
            <button
              disabled={deleteConfirm !== "DELETE"}
              onClick={handleDeleteAccount}
              className="w-full py-3 bg-red-500 text-white rounded-full text-sm font-medium hover:bg-red-600 disabled:opacity-20 transition-all"
            >
              Permanently Delete Account
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
