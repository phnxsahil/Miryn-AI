"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, UserRound, Copy, ArrowRightLeft, TrendingUp, BarChart3, Fingerprint, Layers, Sparkles, Shield, ChevronRight, Activity } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { api } from "@/lib/api";
import type { ComparePayload, CompareReport, DemoPersonaCard } from "@/lib/types";
import { getErrorMessage } from "@/lib/utils";

function percent(value: number | null | undefined) {
  if (typeof value !== "number") return "--";
  return `${Math.round(value * 100)}%`;
}

function score(value: number | null | undefined) {
  if (typeof value !== "number") return "--";
  return value.toFixed(2);
}

function LineChart({
  data,
}: {
  data: Array<{ version: number; left: number; right: number }>;
}) {
  const width = 800;
  const height = 300;
  const padding = 40;
  const maxVersion = Math.max(...data.map((point) => point.version), 1);
  const maxValue = Math.max(...data.flatMap((point) => [point.left, point.right]), 0.65);

  const buildPath = (key: "left" | "right") =>
    data
      .map((point, index) => {
        const x = padding + ((width - padding * 2) * (point.version - 1)) / Math.max(maxVersion - 1, 1);
        const y = height - padding - ((height - padding * 2) * point[key]) / Math.max(maxValue, 0.01);
        return `${index === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");

  return (
    <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] p-8 rounded-[12px] group transition-all shadow-sm" style={{ borderWidth: "0.5px" }}>
      <div className="flex items-center justify-between mb-10">
        <div className="flex items-center gap-3">
           <div className="w-8 h-8 rounded-lg bg-accent/5 flex items-center justify-center">
             <TrendingUp size={14} className="text-accent" />
           </div>
           <span className="mono-label !text-[12px] !text-muted uppercase tracking-[0.3em]">Neural Drift Projection</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-sm bg-[#c8b8ff]" />
            <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest">Active Focus</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-sm bg-[#5c5280]" />
            <span className="mono-label !text-[11px] !text-muted uppercase tracking-widest">Comparison</span>
          </div>
        </div>
      </div>
      
      <div className="relative aspect-[8/3] w-full">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full">
          <defs>
            <linearGradient id="leftGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#c8b8ff" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#c8b8ff" stopOpacity="0" />
            </linearGradient>
          </defs>
          
          {/* Grid Lines */}
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
          
          {data.map((point) => {
            const x = padding + ((width - padding * 2) * (point.version - 1)) / Math.max(maxVersion - 1, 1);
            return (
              <g key={`tick-${point.version}`}>
                <text x={x} y={height - 12} textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="10" className="font-mono">Session {point.version}</text>
                <line x1={x} y1={padding} x2={x} y2={height - padding} stroke="rgba(255,255,255,0.04)" strokeDasharray="4 4" />
              </g>
            );
          })}

           <motion.path 
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 2, ease: "easeInOut" }}
            d={buildPath("left")} 
            fill="none" 
            stroke="#c8b8ff" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
          />
          <motion.path 
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 1 }}
            transition={{ duration: 2, ease: "easeInOut", delay: 0.2 }}
            d={buildPath("right")} 
            fill="none" 
            stroke="#5c5280" 
            strokeWidth="3" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
          />
        </svg>
      </div>
    </div>
  );
}

function MetricBars({
  title,
  leftData,
  rightData,
  icon: Icon
}: {
  title: string;
  leftData: Array<{ label?: string; tier?: string; emotion?: string; count: number }>;
  rightData: Array<{ label?: string; tier?: string; emotion?: string; count: number }>;
  icon?: any
}) {
  const labelFor = (item: { label?: string; tier?: string; emotion?: string }) => item.label || item.tier || item.emotion || "Unknown";
  const labels = Array.from(new Set([...leftData.map(labelFor), ...rightData.map(labelFor)]));
  const max = Math.max(
    ...labels.flatMap((label) => [
      leftData.find((item) => labelFor(item) === label)?.count || 0,
      rightData.find((item) => labelFor(item) === label)?.count || 0,
    ]),
    1,
  );

  return (
    <div className="bg-[#14141f] border border-[rgba(255,255,255,0.06)] p-8 rounded-[12px] group transition-all shadow-sm" style={{ borderWidth: "0.5px" }}>
      <div className="flex items-center gap-3 mb-10">
        <div className="w-8 h-8 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
          {Icon && <Icon size={14} className="text-muted" />}
        </div>
        <span className="mono-label !text-[12px] !text-muted uppercase tracking-[0.3em]">{title}</span>
      </div>
      
      <div className="space-y-8">
        {labels.map((label, idx) => {
          const left = leftData.find((item) => labelFor(item) === label)?.count || 0;
          const right = rightData.find((item) => labelFor(item) === label)?.count || 0;
          return (
            <div key={label} className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-base text-primary font-medium tracking-tight">{label}</span>
                <div className="flex items-center gap-4 text-xs mono-label">
                  <span className="text-[#c8b8ff]">{left}</span>
                  <span className="text-[#3e3d54]">/</span>
                  <span className="text-[#3e3d54]">{right}</span>
                </div>
              </div>
                <div className="w-full">
                <div className="h-2 rounded-full bg-[rgba(255,255,255,0.06)] overflow-hidden relative">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${(left / max) * 100}%` }}
                    transition={{ duration: 1, delay: idx * 0.05 }}
                    className="h-full bg-[#c8b8ff] shadow-[0_0_12px_rgba(200,184,255,0.2)]" 
                  />
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(right / max) * 100}%` }}
                    transition={{ duration: 1, delay: idx * 0.05 + 0.1 }}
                    className="absolute top-0 left-0 h-full bg-[#3d3660]/70 pointer-events-none"
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function CompareWorkspace() {
  const [personas, setPersonas] = useState<DemoPersonaCard[]>([]);
  const [leftUserId, setLeftUserId] = useState("");
  const [rightUserId, setRightUserId] = useState("");
  const [compare, setCompare] = useState<ComparePayload | null>(null);
  const [report, setReport] = useState<CompareReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [detailLevel, setDetailLevel] = useState<"summary" | "detailed">("detailed");
  const [didInitialCompareLoad, setDidInitialCompareLoad] = useState(false);

  const orderedPersonas = useMemo(() => {
    return [...personas].sort((a, b) => a.key.localeCompare(b.key));
  }, [personas]);

  const loadPersonas = async () => {
    const items = await api.getDemoPersonas();
    setPersonas(items);
    if (items.length >= 2) {
      setLeftUserId((current) => current || items[0].user_id);
      setRightUserId((current) => current || items[1].user_id);
    }
    return items;
  };

  const loadComparison = async (leftId: string, rightId: string) => {
    const [compareData, reportData] = await Promise.all([
      api.compareUsers(leftId, rightId),
      api.getComparisonReport(leftId, rightId),
    ]);
    setCompare(compareData);
    setReport(reportData);
  };

  useEffect(() => {
    api.loadToken();
    const bootstrap = async () => {
      try {
        const items = await loadPersonas();
        if (items.length >= 2) {
          await loadComparison(items[0].user_id, items[1].user_id);
          setDidInitialCompareLoad(true);
        }
      } catch (err) {
        setError(getErrorMessage(err, "Failed to load compare workspace"));
      } finally {
        setLoading(false);
      }
    };
    void bootstrap();
  }, []);

  useEffect(() => {
    if (!leftUserId || !rightUserId) return;
    if (!personas.length) return;
    if (!didInitialCompareLoad) return;
    setRefreshing(true);
    void loadComparison(leftUserId, rightUserId)
      .catch((err) => setError(getErrorMessage(err, "Failed to refresh comparison")))
      .finally(() => setRefreshing(false));
  }, [leftUserId, rightUserId, personas.length, didInitialCompareLoad]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void">
        <div className="flex flex-col items-center gap-8">
           <motion.div 
             animate={{ rotate: 360 }}
             transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
             className="w-12 h-12 rounded-full border-t-2 border-accent shadow-[0_0_20px_rgba(139,92,246,0.1)]"
           />
          <div className="mono-label !text-accent uppercase tracking-[0.3em] animate-pulse">Quantifying Divergence...</div>
        </div>
      </div>
    );
  }

  const leftPersona = orderedPersonas.find((persona) => persona.user_id === leftUserId);
  const rightPersona = orderedPersonas.find((persona) => persona.user_id === rightUserId);

  return (
    <div className="min-h-screen bg-void text-primary p-8 md:p-16 relative overflow-x-hidden">
      {/* Background Ambient Glows */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-accent/[0.05] rounded-full blur-[180px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-accent-beta/[0.03] rounded-full blur-[150px] pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-24 flex flex-col md:flex-row md:items-end md:justify-between gap-12 border-b border-white/[0.04] pb-20">
          <div className="space-y-6 max-w-3xl">
            <div className="flex items-center gap-4">
               <ArrowRightLeft className="text-accent w-8 h-8" />
               <h2 className="mono-label !text-accent uppercase tracking-[0.4em]">Comparative Protocol</h2>
            </div>
            <h1 className="text-6xl md:text-9xl font-bold tracking-tighter leading-[0.9]">
              Identity <span className="text-accent">Divergence</span>
            </h1>
            <p className="text-2xl md:text-3xl text-muted editorial-italic leading-relaxed">
              &ldquo;Mapping the structural variance between neural profiles. Quantifying the evolution of the self through interactional drift.&rdquo;
            </p>
          </div>
          
          <div className="flex flex-col items-end gap-3">
             <div className="px-6 py-2.5 rounded-full bg-white/[0.03] border border-white/[0.04]">
               <span className="mono-label !text-[12px] !text-dim uppercase tracking-widest">Resonance Calibration / V2.8</span>
             </div>
          </div>
        </header>

        {/* Node Selection */}
        <section className="mb-20 bg-card border border-white/[0.04] p-10 rounded-[40px] flex flex-col md:flex-row items-start justify-between gap-10">
          <div className="space-y-2">
            <span className="mono-label !text-primary uppercase tracking-widest block">Neural Nodes</span>
            <p className="text-sm text-dim">Select identities to overlay in the divergence matrix</p>
            <div className="flex gap-3 mt-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent/[0.08] border border-accent/15">
                <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                <span className="text-[10px] mono-label text-accent uppercase tracking-widest">Active Node</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.06]">
                <div className="w-1.5 h-1.5 rounded-full bg-white/20" />
                <span className="text-[10px] mono-label text-dim uppercase tracking-widest">Baseline State</span>
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap items-center gap-6">
            <div className="relative group">
              <select
                value={leftUserId}
                onChange={(e) => setLeftUserId(e.target.value)}
                className="appearance-none rounded-2xl border border-white/[0.08] bg-[#1a1a1a] text-primary pl-6 pr-12 py-3.5 text-sm font-medium outline-none transition-all focus:border-accent/40 cursor-pointer"
              >
                {orderedPersonas.map((p) => <option key={p.user_id} value={p.user_id}>{p.label}</option>)}
              </select>
              <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-muted pointer-events-none" size={14} />
            </div>

            <ArrowRightLeft className="text-white/10 hidden md:block" size={18} />

            <div className="relative group">
              <select
                value={rightUserId}
                onChange={(e) => setRightUserId(e.target.value)}
                className="appearance-none rounded-2xl border border-white/[0.08] bg-[#1a1a1a] text-primary pl-6 pr-12 py-3.5 text-sm font-medium outline-none transition-all focus:border-white/20 cursor-pointer"
              >
                {orderedPersonas.map((p) => <option key={p.user_id} value={p.user_id}>{p.label}</option>)}
              </select>
              <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 rotate-90 text-muted pointer-events-none" size={14} />
            </div>
          </div>
        </section>

        {compare && leftPersona && rightPersona && (
          <div className="space-y-24">
            {/* Identity Profiles */}
            <div className="grid md:grid-cols-2 gap-10">
              {[
                { data: compare.left, card: leftPersona, color: "alpha", name: leftPersona.label, role: "Active Identity Node" },
                { data: compare.right, card: rightPersona, color: "beta", name: rightPersona.label, role: "Comparison Baseline" }
              ].map((p, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-6 rounded-[12px] bg-[#14141f] border border-[rgba(255,255,255,0.06)] transition-all duration-700 relative overflow-hidden group min-h-[220px] flex flex-col justify-between"
                  style={{ borderWidth: "0.5px" }}
                >
                  <div className={`absolute top-0 right-0 w-24 h-24 ${p.color === "alpha" ? "bg-[#c8b8ff]/10" : "bg-[#5c5280]/10"} blur-[60px] pointer-events-none group-hover:opacity-150 transition-opacity`} />
                  
                  <div>
                    <div className="flex justify-between items-start mb-4 relative z-10">
                      <div className="flex items-center gap-3">
                         <div className={`w-10 h-10 rounded-lg flex items-center justify-center border text-base font-bold ${p.color === "alpha" ? "bg-[rgba(200,184,255,0.08)] border-[#c8b8ff]/20 text-[#c8b8ff]" : "bg-[rgba(92,82,128,0.2)] border-[#5c5280]/40 text-[#5c5280]"}`}>
                           {p.name[0]}
                         </div>
                         <div>
                           <h3 className="text-lg font-bold tracking-tight text-primary leading-tight">{p.name}</h3>
                           <div className="flex items-center gap-2">
                             <p className={`text-[9px] mono-label ${p.color === "alpha" ? "text-[#c8b8ff]" : "text-[#5c5280]"} uppercase tracking-widest`}>{p.role}</p>
                             <span className="text-[9px] text-dim font-mono">ID: {p.card.user_id.slice(0,8)}</span>
                           </div>
                         </div>
                      </div>
                    </div>

                    <p className="text-base text-primary/70 leading-snug editorial-italic mb-4 line-clamp-2 overflow-hidden">
                      &ldquo;{p.data.profile.goal}&rdquo;
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4 w-full relative z-10 pt-4 border-t border-white/[0.04]">
                    <div>
                      <span className="mono-label !text-[9px] !text-dim uppercase tracking-[0.2em] block mb-0.5">Neural Drift</span>
                      <div className={`text-[28px] font-ui font-bold ${p.color === "alpha" ? "text-[#c8b8ff]" : "text-[#5c5280]"}`}>{percent(p.data.identity_metrics.drift)}</div>
                    </div>
                    <div>
                      <span className="mono-label !text-[9px] !text-dim uppercase tracking-[0.2em] block mb-0.5">Stability</span>
                      <div className="text-2xl font-ui font-bold text-primary">{score(p.data.identity_metrics.stability_score)}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Visual Analytics */}
            <section className="space-y-12">
               <div className="flex items-center gap-8 mb-6">
                 <h2 className="text-3xl font-bold tracking-tight">Quantitative Analytics</h2>
                 <div className="h-[1px] flex-1 bg-white/[0.04]" />
               </div>

               <div className="grid gap-8 lg:grid-cols-2">
                 <LineChart data={compare.charts.drift_timeline} />
                 <MetricBars
                   title="Structure Volume"
                   icon={Layers}
                   
                   
                   leftData={compare.charts.identity_counts.left}
                   rightData={compare.charts.identity_counts.right}
                 />
                 <MetricBars
                   title="Emotional Resilience"
                   icon={Activity}
                   
                   
                   leftData={compare.charts.emotion_distribution.left}
                   rightData={compare.charts.emotion_distribution.right}
                 />
                 <MetricBars
                   title="Cognitive Tiering"
                   icon={Fingerprint}
                   
                   
                   leftData={compare.charts.memory_distribution.left}
                   rightData={compare.charts.memory_distribution.right}
                 />
               </div>
            </section>

            {/* Synthetic Narrative */}
            {report && (
              <section className="pt-32 border-t border-white/[0.03]">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-10 mb-20">
                   <div className="space-y-4">
                     <div className="flex items-center gap-3">
                        <Sparkles className="text-accent" size={24} />
                        <h2 className="mono-label !text-accent !text-sm uppercase tracking-[0.4em]">Synthetic Thesis</h2>
                     </div>
                      <h3 className="text-6xl md:text-8xl font-bold tracking-tighter">Comparative <span className="text-muted">Narrative</span></h3>
                   </div>
                   <button
                      onClick={() => setDetailLevel(detailLevel === 'summary' ? 'detailed' : 'summary')}
                     className="px-8 py-4 rounded-full bg-white/[0.03] border border-white/[0.04] hover:bg-white/[0.05] transition-all"
                    >
                      <span className="mono-label !text-[12px] uppercase tracking-widest">{detailLevel === 'summary' ? 'Expand Synthesis' : 'Contract Summary'}</span>
                    </button>
                </div>

                <div className="grid gap-20 lg:grid-cols-[1fr_0.6fr]">
                   <div className="space-y-16">
                       <div className="bg-card border border-white/[0.04] p-12 rounded-[48px] relative group">
                         <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.05] transition-opacity">
                           <Sparkles size={120} />
                         </div>
                         <span className="mono-label !text-[12px] !text-dim uppercase tracking-[0.4em] block mb-10">Abstract Synthesis</span>
                         <p className="text-3xl md:text-4xl editorial-italic leading-relaxed text-primary">
                           &ldquo;{report.sections.introduction}&rdquo;
                         </p>
                       </div>

                      <div className="space-y-12">
                        {report.sections.comparison_dimensions.slice(0, detailLevel === "summary" ? 2 : undefined).map((s, idx) => (
                          <motion.div 
                            key={idx}
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="space-y-6 pl-12 border-l border-white/[0.05] relative"
                          >
                            <div className="absolute left-0 top-0 -translate-x-1/2 w-4 h-4 rounded-full bg-white border border-accent" />
                            <div className="space-y-1">
                              <span className="mono-label !text-[12px] !text-accent uppercase tracking-widest">Dimension 0{idx + 1}</span>
                              <h4 className="text-2xl font-bold tracking-tight">{s.title}</h4>
                            </div>
                             <p className="text-muted leading-relaxed text-xl">
                               {s.body}
                            </p>
                          </motion.div>
                        ))}
                      </div>
                   </div>

                   <aside className="space-y-10">
                      <div className="bg-accent/[0.03] border border-accent/10 p-10 rounded-[40px] space-y-10 shadow-sm">
                         <div className="space-y-4">
                           <span className="mono-label !text-accent !text-xs uppercase tracking-widest">Drift Analysis</span>
                            <p className="text-base leading-relaxed text-muted">
                              {report.sections.drift_analysis}
                           </p>
                         </div>
                         <div className="h-[1px] bg-accent/10" />
                         <div className="space-y-4">
                           <span className="mono-label !text-accent !text-xs uppercase tracking-widest">Architectural Standout</span>
                            <p className="text-xl leading-relaxed text-primary font-medium">
                              &ldquo;{report.sections.miryn_standout}&rdquo;
                           </p>
                         </div>
                      </div>

                       <div className="bg-card border border-white/[0.04] p-10 rounded-[40px] flex items-center gap-6">
                         <div className="w-12 h-12 rounded-full bg-white/[0.03] border border-white/[0.04] flex items-center justify-center shrink-0">
                           <Shield size={20} className="text-dim" />
                         </div>
                        <p className="text-[12px] text-muted uppercase tracking-widest leading-loose font-medium">
                          All comparative data is synthesized locally through an identity-aware persistence layer.
                        </p>
                      </div>
                   </aside>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
