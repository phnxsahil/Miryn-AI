"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Menu, X, MessageSquare, Fingerprint, Archive, Settings, Plus, Layers, User } from "lucide-react";
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
  const [authChecked, setAuthChecked] = useState(false);
  const [user, setUser] = useState<{ email?: string; first_name?: string } | null>(null);

  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
  const closeMenu = () => setIsMenuOpen(false);

  const navLinkClass = (href: string) => {
    const isActive = pathname.startsWith(href);
    return `group flex items-center gap-4 py-3.5 px-5 rounded-2xl transition-all duration-300 relative ${
      isActive
        ? "text-[#c8b8ff]"
        : "text-[#4a4868] hover:text-[#ede9ff]"
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
      <header className="md:hidden border-b border-white/[0.05] p-6 flex items-center justify-between sticky top-0 bg-void/90 backdrop-blur-xl z-40">
        <div className="text-2xl font-bold tracking-tight text-[#c8b8ff]">Miryn</div>
        <button
          onClick={toggleMenu}
          className="p-2 text-dim hover:text-primary transition-colors"
          aria-label="Toggle menu"
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </header>

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 transform transition-all duration-500 cubic-bezier(0.4, 0, 0.2, 1)
          md:relative md:translate-x-0 md:inset-auto md:w-80 lg:w-96 flex flex-col
          bg-[#0f0f17] border-r border-white/[0.04]
          ${isMenuOpen ? "translate-x-0 w-[300px]" : "-translate-x-full md:translate-x-0"}
        `}
      >
        {/* Branding */}
        <div className="p-10 flex items-center justify-between">
          <Link href="/chat" className="text-3xl font-bold tracking-tighter text-[#c8b8ff] flex items-center gap-3 group">
            Miryn 
            <span className="text-xs mono-label text-dim border border-white/[0.06] px-2.5 py-1 rounded-full group-hover:border-accent/20 transition-colors">v1.0</span>
          </Link>
          <button onClick={closeMenu} className="md:hidden p-2 text-dim hover:text-primary">
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-4 custom-scrollbar pb-10">
          <nav className="space-y-2 mt-4 px-2">
            {[
              { href: "/chat", icon: MessageSquare, label: "Conversations" },
              { href: "/identity", icon: Fingerprint, label: "Identity Layer" },
              { href: "/memory", icon: Archive, label: "Memory Bank" },
              { href: "/onboarding", icon: Layers, label: "Calibration" },
              { href: "/settings", icon: Settings, label: "System Settings" },
            ].map((item) => (
              <Link key={item.href} href={item.href} onClick={closeMenu} className={navLinkClass(item.href)}>
                <item.icon size={22} className={pathname.startsWith(item.href) ? "text-accent" : "text-current"} />
                <span className="font-bold text-[15px]">{item.label}</span>
                {pathname.startsWith(item.href) && (
                  <motion.div 
                    layoutId="nav-pill"
                    className="absolute inset-0 bg-[rgba(200,184,255,0.08)] rounded-2xl border-l-2 border-l-[#c8b8ff] -z-10"
                  />
                )}
              </Link>
            ))}
          </nav>

          {/* Chat History Section */}
          <div className="mt-16 space-y-6">
            <div className="px-6 flex items-center justify-between">
              <span className="mono-label !text-[#3e3d54] !text-[11px] tracking-[0.2em] uppercase">Recent Reflective Sessions</span>
              <button 
                onClick={() => { api.createConversation().then(c => router.push(`/chat?id=${c.id}`)); closeMenu(); }}
                className="w-8 h-8 flex items-center justify-center rounded-full text-[#4a4868] hover:text-[#c8b8ff] transition-colors"
                title="New Conversation"
              >
                <Plus size={16} />
              </button>
            </div>
            
            <div className="min-h-0">
              <ConversationList onItemClick={closeMenu} />
            </div>
          </div>
        </div>

        {/* User Footer */}
        <div className="p-8 mt-auto border-t border-white/[0.04] bg-[#0f0f17]">
          <div className="group flex items-center gap-4 p-4 rounded-[24px] hover:bg-white/[0.03] transition-all cursor-pointer border border-transparent hover:border-white/[0.06]">
            <div className="w-12 h-12 rounded-full bg-[rgba(200,184,255,0.12)] text-[#c8b8ff] flex items-center justify-center text-lg font-bold">
              {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || <User size={22} />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-[15px] font-medium truncate text-[#ede9ff]">
                {user?.first_name || "Authorized User"}
              </div>
              <div className="text-[11px] mono-label truncate text-[#3e3d54] uppercase tracking-widest">
                {user?.email || "alpha-access-v1"}
              </div>
            </div>
            <div className="w-10 h-10 flex items-center justify-center text-[#4a4868] group-hover:text-[#c8b8ff] transition-colors">
              <Settings size={18} />
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile Backdrop */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-md z-40 md:hidden" 
            onClick={closeMenu} 
          />
        )}
      </AnimatePresence>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 relative flex flex-col h-screen overflow-hidden bg-[#0f0f17]">
        {/* Subtle background texture/glow */}
        <div className="absolute inset-0 bg-[#0f0f17] -z-20" />
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-accent/[0.03] rounded-full blur-[150px] pointer-events-none -z-10" />
        
        <div className="flex-1 overflow-y-auto custom-scrollbar relative z-10">
          {children}
        </div>
      </main>
    </div>
  );
}
