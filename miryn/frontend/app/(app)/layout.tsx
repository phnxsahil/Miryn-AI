"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu, X, MessageSquare, Fingerprint, Archive, Settings, Plus, Layers, User, PanelLeftClose, PanelLeftOpen, HeartPulse } from "lucide-react";
import ConversationList from "@/components/Chat/ConversationList";
import { api } from "@/lib/api";
import { useChatStore } from "@/lib/store";
import { motion, AnimatePresence } from "framer-motion";
import LoadingState from "@/components/ui/LoadingState";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<{ email?: string; full_name?: string | null } | null>(null);
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const chatLoading = useChatStore((state) => state.loading);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);
  const toggleDesktopSidebar = () => setIsDesktopSidebarOpen(!isDesktopSidebarOpen);
  const createConversation = () => {
    if (chatLoading) return;
    const chat = useChatStore.getState();
    chat.setMessages([]);
    chat.setConversationId(null);
    chat.setStatus(null);
    chat.setStreaming(false);
    chat.setStreamingIndex(null);
    router.push("/chat");
    closeMenu();
  };

  const navLinkClass = (href: string) => {
    const isActive = pathname.startsWith(href);
    return `group flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-200 relative ${
      isActive
        ? "bg-[color:var(--theme-overlay)] text-[color:var(--theme-text)] font-medium"
        : "text-[color:var(--theme-dim)] hover:bg-[color:var(--theme-overlay)] hover:text-[color:var(--theme-text)]"
    }`;
  };

  useEffect(() => {
    let mounted = true;

    api.ensureAuthenticated()
      .then((authenticated) => {
        if (!mounted) return;
        if (!authenticated) {
          router.replace("/login");
          return;
        }
        api.getMe().then(u => {
          if (mounted) setUser(u);
        }).catch(() => null);
        setAuthChecked(true);
      })
      .catch(() => {
        if (mounted) {
          router.replace("/login");
        }
      });

    return () => {
      mounted = false;
    };
  }, [router]);

  useEffect(() => {
    const closeAccountMenu = (event: MouseEvent) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target as Node)) setIsAccountMenuOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsAccountMenuOpen(false);
    };
    document.addEventListener("mousedown", closeAccountMenu);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeAccountMenu);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, []);

  if (!authChecked) {
    return <LoadingState label="Initializing your account..." />;
  }

  return (
    <div className="h-[100dvh] bg-[color:var(--theme-bg)] text-[color:var(--theme-text)] flex flex-col md:flex-row font-ui overflow-hidden">
      {/* Mobile Header */}
      <header className="md:hidden border-b border-[color:var(--theme-border)] px-3 py-2 flex items-center justify-between bg-[color:var(--theme-bg)] z-40">
        <button
          onClick={toggleMenu}
          className="p-2 text-[color:var(--theme-dim)] hover:text-[color:var(--theme-text)] transition-colors"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <div className="text-base font-semibold tracking-tight text-[color:var(--theme-text)]">Miryn</div>
        <button
          onClick={createConversation}
          disabled={chatLoading}
          className="p-2 text-[color:var(--theme-dim)] hover:text-[color:var(--theme-text)] transition-colors"
          aria-label="New chat"
        >
          <Plus size={20} />
        </button>
      </header>

      {/* Desktop Toggle Button (when sidebar is closed) */}
      {!isDesktopSidebarOpen && (
        <button
          onClick={toggleDesktopSidebar}
          className="hidden md:flex absolute top-4 left-4 z-50 p-2 text-[color:var(--theme-dim)] hover:text-[color:var(--theme-text)] transition-colors bg-[color:var(--theme-bg)] rounded-md border border-[color:var(--theme-border)] shadow-sm"
          title="Open sidebar"
        >
          <PanelLeftOpen size={20} />
        </button>
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 flex w-[292px] flex-col bg-[color:var(--theme-sidebar)] transition-transform duration-200
          md:relative md:translate-x-0 md:transition-none
          ${isMenuOpen ? "translate-x-0" : "-translate-x-full"}
          ${!isDesktopSidebarOpen ? "md:hidden" : "md:flex"}
        `}
      >
        {/* Top Actions Area */}
        <div className="p-3 flex items-center justify-between">
           <button
            onClick={toggleDesktopSidebar}
            className="hidden md:flex p-2 text-dim hover:text-primary transition-colors hover:bg-[color:var(--theme-overlay)] rounded-md"
            title="Close sidebar"
          >
            <PanelLeftClose size={20} />
          </button>

          <button
            onClick={createConversation}
            disabled={chatLoading}
            className="flex-1 ml-2 flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg text-primary hover:bg-[color:var(--theme-overlay)] transition-colors border border-[color:var(--theme-border)] justify-between disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span>New Chat</span>
            <Plus size={16} className="text-dim" />
          </button>

          <button onClick={closeMenu} className="md:hidden p-2 text-dim hover:text-primary ml-2">
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-3 custom-scrollbar pb-6 flex flex-col gap-6">
          {/* Main Links */}
          <nav className="space-y-1 mt-2">
            {[
              { href: "/chat", icon: MessageSquare, label: "Chat" },
              { href: "/identity", icon: Fingerprint, label: "Identity" },
              { href: "/memory", icon: Archive, label: "Memory" },
              { href: "/sanctuary", icon: HeartPulse, label: "Sanctuary" },
              { href: "/onboarding", icon: Layers, label: "Getting started" },
              { href: "/settings", icon: Settings, label: "Settings" },
            ].map((item) => (
              <Link key={item.href} href={item.href} onClick={closeMenu} className={navLinkClass(item.href)}>
                <item.icon size={18} className={pathname.startsWith(item.href) ? "text-primary" : "text-dim group-hover:text-primary"} />
                <span className="text-sm">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Chat History Section */}
          <div className="flex-1 flex flex-col min-h-0">



            <div className="flex-1 min-h-0 -mx-3">
              <ConversationList onItemClick={closeMenu} />
            </div>
          </div>
        </div>

        {/* User Footer */}
        <div ref={accountMenuRef} className="sidebar-account relative p-3 mt-auto border-t bg-[color:var(--theme-sidebar)]">
          {isAccountMenuOpen && (
            <div role="menu" className="absolute bottom-[calc(100%-8px)] start-3 end-3 rounded-xl border border-[color:var(--theme-border)] bg-[color:var(--theme-card)] p-1.5 shadow-xl">
              <Link href="/settings" role="menuitem" onClick={() => { setIsAccountMenuOpen(false); closeMenu(); }} className="flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)]">
                <Settings size={14} /> Settings
              </Link>
              <button type="button" role="menuitem" onClick={() => { api.logout(); setIsAccountMenuOpen(false); router.replace("/login"); }} className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs text-[color:var(--theme-text)] hover:bg-[color:var(--theme-overlay)]">
                <User size={14} /> Log out
              </button>
            </div>
          )}
          <button type="button" aria-label="Account menu" aria-expanded={isAccountMenuOpen} onClick={() => setIsAccountMenuOpen((open) => !open)} className="group flex w-full items-center gap-3 rounded-lg p-2 text-left transition-all hover:bg-[color:var(--theme-overlay)]">
            <div className="flex h-8 w-8 items-center justify-center rounded-full border border-accent/20 bg-accent/10 text-sm font-bold text-accent">
              {user?.full_name?.trim()?.[0]?.toUpperCase() || user?.email?.trim()?.[0]?.toUpperCase() || "M"}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-primary">{user?.full_name || user?.email || "Account"}</div>
              <div className="truncate text-[11px] text-[color:var(--theme-dim)]">Account</div>
            </div>
            <User size={16} className="text-[color:var(--theme-dim)] transition-colors group-hover:text-[color:var(--theme-text)]" />
          </button>
        </div>
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-[color-mix(in_srgb,var(--theme-bg)_80%,transparent)] backdrop-blur-sm z-40 md:hidden"
            onClick={closeMenu} 
          />
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <main className="flex-1 min-h-0 min-w-0 relative flex flex-col overflow-hidden bg-[color:var(--theme-bg)]">
        <div className="flex-1 min-h-0 overflow-y-auto relative z-10 w-full">
          {children}
        </div>
      </main>
    </div>
  );
}
