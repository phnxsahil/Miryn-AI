"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { getErrorMessage } from "@/lib/utils";

export default function SettingsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleLogout = async () => {
    await api.logout();
    window.location.href = "/login";
  };

  const handleDeleteAccount = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.deleteAccount();
      await api.logout();
      window.location.href = "/login";
    } catch (err) {
      setError(getErrorMessage(err, "Failed to delete account"));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <div className="space-y-12">
        <header>
          <h1 className="text-3xl font-serif font-light text-white">Settings</h1>
          <p className="text-secondary mt-2">Manage your account and preferences.</p>
        </header>

        <section className="space-y-6">
          <h2 className="text-sm uppercase tracking-[0.2em] text-secondary">Account</h2>
          
          <div className="rounded-2xl border border-white/10 bg-black/30 p-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Log out</div>
                <div className="text-xs text-secondary mt-1">Sign out of your current session.</div>
              </div>
              <button 
                onClick={handleLogout}
                className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 transition-colors"
              >
                Log out
              </button>
            </div>

            <div className="pt-6 border-t border-white/5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-red-400 font-medium">Delete Account</div>
                  <div className="text-xs text-secondary mt-1">Permanently remove your account and all data. This cannot be undone.</div>
                </div>
                {!showDeleteConfirm ? (
                  <button 
                    onClick={() => setShowDeleteConfirm(true)}
                    className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm hover:bg-red-500/20 transition-colors"
                  >
                    Delete...
                  </button>
                ) : (
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => setShowDeleteConfirm(false)}
                      className="text-xs text-secondary hover:text-white"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={handleDeleteAccount}
                      disabled={loading}
                      className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm hover:bg-red-700 transition-colors disabled:opacity-50"
                    >
                      {loading ? "Deleting..." : "Confirm Delete"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20 text-green-200 text-sm">
            {success}
          </div>
        )}
      </div>
    </div>
  );
}
