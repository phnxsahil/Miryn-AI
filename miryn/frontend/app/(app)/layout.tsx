"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu, X } from "lucide-react";
import ConversationList from "@/components/Chat/ConversationList";
import { api } from "@/lib/api";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);

  useEffect(() => {
    let mounted = true;

    api.ensureAuthenticated()
      .then((authenticated) => {
        if (!mounted) return;
        if (!authenticated) {
          router.replace("/login");
        } else {
          void api.getMe().catch(() => null);
        }
      })
      .finally(() => {
        if (mounted) {
          setAuthChecked(true);
        }
      });

    return () => {
      mounted = false;
    };
  }, [router]);

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-void text-secondary flex items-center justify-center">
        Authenticating...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void text-white flex flex-col md:flex-row">
      <header className="md:hidden border-b border-white/10 p-4 flex items-center justify-between sticky top-0 bg-void z-40">
        <div className="text-xl font-light tracking-wide">Miryn</div>
        <button
          onClick={toggleMenu}
          className="p-2 text-secondary hover:text-white"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </header>

      <aside
        className={`
        fixed inset-0 z-50 transform transition-transform duration-300 ease-in-out bg-void border-r border-white/10 p-6
        md:relative md:translate-x-0 md:inset-auto md:w-64 lg:w-72 md:block
        ${isMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
      `}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="text-xl font-light tracking-wide">Miryn</div>
          <button onClick={closeMenu} className="md:hidden p-2 text-secondary hover:text-white">
            <X size={24} />
          </button>
        </div>

        <nav className="space-y-3 text-sm text-secondary">
          <Link
            className="block py-2 px-3 rounded-xl hover:bg-white/5 hover:text-white transition-colors"
            href="/chat"
            onClick={closeMenu}
          >
            Chat
          </Link>
          <Link
            className="block py-2 px-3 rounded-xl hover:bg-white/5 hover:text-white transition-colors"
            href="/onboarding"
            onClick={closeMenu}
          >
            Onboarding
          </Link>
          <Link
            className="block py-2 px-3 rounded-xl hover:bg-white/5 hover:text-white transition-colors"
            href="/identity"
            onClick={closeMenu}
          >
            Identity
          </Link>
          <Link
            className="block py-2 px-3 rounded-xl hover:bg-white/5 hover:text-white transition-colors"
            href="/memory"
            onClick={closeMenu}
          >
            Memory
          </Link>
          <Link
            className="block py-2 px-3 rounded-xl hover:bg-white/5 hover:text-white transition-colors"
            href="/settings"
            onClick={closeMenu}
          >
            Settings
          </Link>
        </nav>

        <div className="mt-8 overflow-y-auto">
          <div className="px-3 text-[10px] uppercase tracking-[0.2em] text-secondary mb-4 flex items-center justify-between">
            <span>Recent Chat</span>
            <Link href="/chat" onClick={closeMenu} className="hover:text-white transition-colors">
              <X size={12} className="rotate-45" />
            </Link>
          </div>
          <ConversationList onItemClick={closeMenu} />
        </div>
      </aside>

      {isMenuOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 md:hidden" onClick={closeMenu} />
      )}

      <main className="flex-1 min-h-0 overflow-hidden">{children}</main>
    </div>
  );
}
