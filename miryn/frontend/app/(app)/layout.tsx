"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu, X, MessageSquare, Fingerprint, Archive, Settings, Plus, Layers, User, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import ConversationList from "@/components/Chat/ConversationList";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isDesktopSidebarOpen, setIsDesktopSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<{ email?: string; first_name?: string } | null>(null);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);
  const toggleDesktopSidebar = () => setIsDesktopSidebarOpen(!isDesktopSidebarOpen);

  const navLinkClass = (href: string) => {
    const isActive = pathname.startsWith(href);
    return `group flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-200 relative ${
      isActive
        ? "bg-white/[0.08] text-white font-medium"
        : "text-dim hover:bg-white/[0.04] hover:text-primary"
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
    const mediaQuery = window.matchMedia("(max-width: 767px)");
    const updateViewport = () => setIsMobile(mediaQuery.matches);
    updateViewport();
    mediaQuery.addEventListener("change", updateViewport);
    return () => mediaQuery.removeEventListener("change", updateViewport);
  }, []);

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-void flex items-center justify-center font-ui">
        <div className="flex flex-col items-center gap-6">
          <div className="relative">
            <div className="w-16 h-16 border-2 border-accent/10 border-t-accent rounded-full animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            </div>
          </div>
          <span className="mono-label !text-accent/60 !tracking-[0.3em] uppercase">Initializing Identity</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-void text-primary flex flex-col md:flex-row font-ui overflow-hidden">
      {/* Mobile Header */}
      <header className="md:hidden border-b border-white/[0.05] p-4 flex items-center justify-between sticky top-0 bg-void/90 backdrop-blur-xl z-40">
        <button
          onClick={toggleMenu}
          className="p-2 text-dim hover:text-primary transition-colors"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <div className="text-lg font-semibold tracking-tight text-[#c8b8ff]">Miryn</div>
        <button
          onClick={() => { api.createConversation().then(c => router.push(`/chat?id=${c.id}`)); }}
          className="p-2 text-dim hover:text-primary transition-colors"
        >
          <Plus size={20} />
        </button>
      </header>

      {/* Desktop Toggle Button (when sidebar is closed) */}
      {!isDesktopSidebarOpen && (
        <button
          onClick={toggleDesktopSidebar}
          className="hidden md:flex absolute top-4 left-4 z-50 p-2 text-dim hover:text-primary transition-colors bg-void rounded-md border border-white/5 shadow-sm"
          title="Open sidebar"
        >
          <PanelLeftOpen size={20} />
        </button>
      )}

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isMobile ? 260 : isDesktopSidebarOpen ? 260 : 0,
          x: isMobile ? (isMenuOpen ? 0 : -260) : 0,
        }}
        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
        className={`
          fixed inset-y-0 left-0 z-50 flex flex-col
          bg-[#0f0f17] border-r border-white/[0.04]
          md:relative md:translate-x-0
          ${isMenuOpen ? "translate-x-0 w-[260px]" : "-translate-x-full md:translate-x-0"}
          ${!isDesktopSidebarOpen && "md:hidden"}
        `}
      >
        {/* Top Actions Area */}
        <div className="p-3 flex items-center justify-between">
           <button
            onClick={toggleDesktopSidebar}
            className="hidden md:flex p-2 text-dim hover:text-primary transition-colors hover:bg-white/[0.04] rounded-md"
            title="Close sidebar"
          >
            <PanelLeftClose size={20} />
          </button>

          <button
            onClick={() => { api.createConversation().then(c => router.push(`/chat?id=${c.id}`)); closeMenu(); }}
            className="flex-1 ml-2 flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg text-primary hover:bg-white/[0.04] transition-colors border border-white/[0.04] justify-between"
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
              { href: "/identity", icon: Fingerprint, label: "Identity Layer" },
              { href: "/memory", icon: Archive, label: "Memory Bank" },
              { href: "/onboarding", icon: Layers, label: "Calibration" },
            ].map((item) => (
              <Link key={item.href} href={item.href} onClick={closeMenu} className={navLinkClass(item.href)}>
                <item.icon size={18} className={pathname.startsWith(item.href) ? "text-primary" : "text-dim group-hover:text-primary"} />
                <span className="text-sm">{item.label}</span>
              </Link>
            ))}
          </nav>

          {/* Chat History Section */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-2 mb-2">
              <span className="text-[11px] font-semibold text-dim uppercase tracking-wider">Today</span>
            </div>
            <div className="flex-1 min-h-0 -mx-3">
              <ConversationList onItemClick={closeMenu} />
            </div>
          </div>
        </div>

        {/* User Footer */}
        <div className="p-3 mt-auto border-t border-white/[0.04] bg-[#0f0f17]">
          <Link href="/settings" onClick={closeMenu} className="group flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.04] transition-all cursor-pointer w-full">
            <div className="w-8 h-8 rounded-full bg-accent/10 text-accent flex items-center justify-center text-sm font-bold border border-accent/20">
              {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || <User size={16} />}
            </div>
            <div className="flex-1 min-w-0 text-left">
              <div className="text-sm font-medium truncate text-primary">
                {user?.first_name || "User"}
              </div>
            </div>
            <div className="text-dim group-hover:text-primary transition-colors px-1">
              <Settings size={16} />
            </div>
          </Link>
        </div>
      </motion.aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40 md:hidden"
            onClick={closeMenu} 
          />
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 relative flex flex-col h-screen overflow-hidden bg-void">
        <div className="flex-1 overflow-y-auto relative z-10 w-full h-full">
          {children}
        </div>
      </main>
    </div>
  );
}
