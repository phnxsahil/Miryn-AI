"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, UserRound, Copy, ArrowRightLeft, TrendingUp, BarChart3, Fingerprint, Layers } from "lucide-react";

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
  leftLabel,
  rightLabel,
}: {
  data: Array<{ version: number; left: number; right: number }>;
  leftLabel: string;
  rightLabel: string;
}) {
  const width = 760;
  const height = 240;
  const padding = 32;
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
    <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6 backdrop-blur-md">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.4em] text-secondary mb-6">
        <div className="flex items-center gap-2">
          <TrendingUp size={12} className="text-accent" />
          <span>Semantic Drift Analysis</span>
        </div>
        <div className="flex items-center gap-4 tracking-normal">
          <span className="flex items-center gap-2 text-white/80"><span className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(200,184,154,0.5)]" />{leftLabel}</span>
          <span className="flex items-center gap-2 text-white/80"><span className="h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)]" />{rightLabel}</span>
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        <defs>
          <linearGradient id="leftGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c8b89a" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#c8b89a" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="rightGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
        {data.map((point) => {
          const x = padding + ((width - padding * 2) * (point.version - 1)) / Math.max(maxVersion - 1, 1);
          return (
            <g key={`tick-${point.version}`}>
              <text x={x} y={height - 8} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="9" className="font-mono">
                V{point.version}
              </text>
            </g>
          );
        })}
        <path d={buildPath("left")} fill="none" stroke="#c8b89a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d={buildPath("right")} fill="none" stroke="#22d3ee" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

function MetricBars({
  title,
  leftLabel,
  rightLabel,
  leftData,
  rightData,
  icon: Icon
}: {
  title: string;
  leftLabel: string;
  rightLabel: string;
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
    <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-6 backdrop-blur-md">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.4em] text-secondary mb-8">
        <div className="flex items-center gap-2">
          {Icon && <Icon size={12} className="text-accent/60" />}
          <span>{title}</span>
        </div>
      </div>
      <div className="space-y-6">
        {labels.map((label) => {
          const left = leftData.find((item) => labelFor(item) === label)?.count || 0;
          const right = rightData.find((item) => labelFor(item) === label)?.count || 0;
          return (
            <div key={label} className="space-y-3">
              <div className="flex items-center justify-between text-[11px] text-white/90 tracking-wide font-light">
                <span>{label}</span>
                <span className="text-[10px] text-secondary/60 font-mono italic">{left} / {right}</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-accent/40" style={{ width: `${(left / max) * 100}%` }} />
                </div>
                <div className="h-1 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full bg-cyan-400/40" style={{ width: `${(right / max) * 100}%` }} />
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
    if (!leftUserId || !rightUserId || leftUserId === rightUserId) return;
    if (!personas.length) return;
    setRefreshing(true);
    void loadComparison(leftUserId, rightUserId)
      .catch((err) => setError(getErrorMessage(err, "Failed to refresh comparison")))
      .finally(() => setRefreshing(false));
  }, [leftUserId, rightUserId, personas.length]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-void text-secondary">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full border-t-2 border-accent animate-spin" />
          <div className="text-[10px] uppercase tracking-widest animate-pulse">Analyzing Divergence...</div>
        </div>
      </div>
    );
  }

  const leftPersona = orderedPersonas.find((persona) => persona.user_id === leftUserId);
  const rightPersona = orderedPersonas.find((persona) => persona.user_id === rightUserId);

  return (
    <div className="min-h-screen bg-void text-white">
      <div className="mx-auto max-w-7xl px-4 md:px-8 py-8 md:py-16">
        {/* Header */}
        <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between border-b border-white/5 pb-12 mb-12">
          <div className="space-y-4">
            <div className="text-[10px] uppercase tracking-[0.5em] text-accent font-medium">Identity Comparative Analysis</div>
            <div>
              <h1 className="text-4xl md:text-6xl font-serif font-extralight tracking-tight">Miryn Thesis: <span className="italic">Divergence</span></h1>
              <p className="mt-4 max-w-2xl text-sm md:text-base text-secondary font-light leading-relaxed">
                A multi-dimensional comparison of Persona Alpha and Persona Beta. This workspace quantifies how identical base models drift into unique identities through lived interaction.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
             <div className="rounded-full border border-white/5 bg-white/[0.03] px-6 py-2.5 text-[10px] uppercase tracking-widest text-secondary/80">
               Project Defense / V2.4
             </div>
          </div>
        </div>

        {/* Selection Controls */}
        <section className="mb-12 rounded-3xl border border-white/5 bg-white/[0.01] p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1">
              <div className="text-[10px] uppercase tracking-[0.3em] text-secondary">Active Nodes</div>
              <div className="text-xs text-white/50 italic">Select identities to overlay in the matrix</div>
            </div>
            <div className="flex flex-wrap items-center gap-4">
              <select
                value={leftUserId}
                onChange={(event) => setLeftUserId(event.target.value)}
                className="rounded-2xl border border-white/10 bg-black/40 px-6 py-3 text-sm text-accent font-light outline-none transition focus:border-accent/40"
              >
                {orderedPersonas.map((persona) => (
                  <option key={persona.user_id} value={persona.user_id}>{persona.label}</option>
                ))}
              </select>
              <div className="text-white/20">
                <ArrowRightLeft size={16} />
              </div>
              <select
                value={rightUserId}
                onChange={(event) => setRightUserId(event.target.value)}
                className="rounded-2xl border border-white/10 bg-black/40 px-6 py-3 text-sm text-cyan-400 font-light outline-none transition focus:border-cyan-400/40"
              >
                {orderedPersonas.map((persona) => (
                  <option key={persona.user_id} value={persona.user_id}>{persona.label}</option>
                ))}
              </select>
            </div>
          </div>
        </section>

        {compare && leftPersona && rightPersona && (
          <div className="space-y-16">
            {/* Persona Cards */}
            <section className="grid gap-6 md:grid-cols-2">
              {[compare.left, compare.right].map((persona, index) => {
                const isLeft = index === 0;
                const accentBorder = isLeft ? "border-accent/20" : "border-cyan-400/20";
                const accentText = isLeft ? "text-accent" : "text-cyan-400";
                const card = isLeft ? leftPersona : rightPersona;
                return (
                  <div key={persona.profile.user_id} className={`rounded-3xl border ${accentBorder} bg-white/[0.01] p-8 group hover:bg-white/[0.02] transition-all duration-700`}>
                    <div className="flex flex-col gap-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-secondary">
                          <Fingerprint size={12} className={accentText} />
                          {card.label}
                        </div>
                        <div className={`text-[10px] font-mono ${accentText} opacity-40 uppercase tracking-tighter`}>
                          ID: {card.user_id.slice(0,8)}...
                        </div>
                      </div>
                      <div>
                        <h2 className="text-2xl font-serif font-light group-hover:text-white transition-colors">{persona.profile.subtitle}</h2>
                        <p className="mt-4 text-xs md:text-sm text-secondary font-light leading-relaxed line-clamp-3 italic">
                          "{persona.profile.goal}"
                        </p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                          <div className="text-[9px] uppercase tracking-[0.2em] text-secondary/50">Drift</div>
                          <div className={`mt-2 text-xl font-serif ${accentText}`}>{percent(persona.identity_metrics.drift)}</div>
                        </div>
                        <div className="rounded-2xl border border-white/5 bg-black/30 p-4">
                          <div className="text-[9px] uppercase tracking-[0.2em] text-secondary/50">Stability</div>
                          <div className="mt-2 text-xl font-serif text-white/90">{score(persona.identity_metrics.stability_score)}</div>
                        </div>
                      </div>
                      <Link 
                        href={`/compare/persona/${card.user_id}?view=identity`}
                        className="mt-2 inline-flex items-center justify-center rounded-xl border border-white/5 bg-white/5 py-3 text-[10px] uppercase tracking-widest text-secondary hover:text-white hover:bg-white/10 transition-all"
                      >
                        Inspect Neural State
                      </Link>
                    </div>
                  </div>
                );
              })}
            </section>

            {/* Charts Section */}
            <section className="space-y-8">
              <div className="flex items-center gap-4 mb-8">
                <h2 className="text-[10px] uppercase tracking-[0.5em] text-secondary whitespace-nowrap">Quantitative Divergence</h2>
                <div className="h-[1px] w-full bg-white/5" />
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <LineChart data={compare.charts.drift_timeline} leftLabel={leftPersona.label} rightLabel={rightPersona.label} />
                <MetricBars
                  title="Identity Matrix Volume"
                  icon={Layers}
                  leftLabel={leftPersona.label}
                  rightLabel={rightPersona.label}
                  leftData={compare.charts.identity_counts.left}
                  rightData={compare.charts.identity_counts.right}
                />
                <MetricBars
                  title="Emotional Resonances"
                  icon={BarChart3}
                  leftLabel={leftPersona.label}
                  rightLabel={rightPersona.label}
                  leftData={compare.charts.emotion_distribution.left}
                  rightData={compare.charts.emotion_distribution.right}
                />
                <MetricBars
                   title="Cognitive Tiered Memory"
                   icon={Fingerprint}
                   leftLabel={leftPersona.label}
                   rightLabel={rightPersona.label}
                   leftData={compare.charts.memory_distribution.left}
                   rightData={compare.charts.memory_distribution.right}
                />
              </div>
            </section>

            {/* Report Section */}
            {report && (
              <section className="mt-20 border-t border-white/5 pt-20">
                <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between mb-12">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.5em] text-accent mb-2">Synthetic Narrative</div>
                    <h3 className="text-3xl font-serif font-extralight tracking-tight">Thesis Discussion Report</h3>
                  </div>
                  <div className="flex gap-4">
                     <button
                        onClick={() => setDetailLevel(detailLevel === 'summary' ? 'detailed' : 'summary')}
                        className="rounded-full border border-white/10 bg-white/5 px-6 py-2 text-[10px] uppercase tracking-widest text-secondary hover:text-white transition-all"
                      >
                        {detailLevel === 'summary' ? 'Expand Details' : 'Contract Summary'}
                      </button>
                  </div>
                </div>

                <div className="grid gap-12 lg:grid-cols-[1fr_0.7fr]">
                  <div className="space-y-12">
                    <div className="prose prose-invert max-w-none">
                      <div className="text-[10px] uppercase tracking-[0.3em] text-secondary/40 mb-4 font-mono">Abstract</div>
                      <p className="text-lg font-serif font-light leading-relaxed text-white/90 italic">
                        {report.sections.introduction}
                      </p>
                    </div>

                    <div className="space-y-10">
                      {report.sections.comparison_dimensions.slice(0, detailLevel === "summary" ? 2 : undefined).map((section, idx) => (
                        <div key={idx} className="space-y-4">
                          <div className="flex items-center gap-4">
                            <span className="text-[9px] font-mono text-accent">0{idx + 1}</span>
                            <h4 className="text-sm font-medium tracking-widest uppercase text-white/80">{section.title}</h4>
                          </div>
                          <p className="text-sm leading-relaxed text-secondary font-light pl-10 border-l border-white/5">
                            {section.body}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-8">
                    <div className="rounded-3xl border border-white/5 bg-white/[0.02] p-8">
                       <h4 className="text-[10px] uppercase tracking-[0.3em] text-secondary mb-6">Comparative Drift Summary</h4>
                       <p className="text-xs leading-relaxed text-white/70 font-light mb-8 italic border-b border-white/5 pb-8">
                         {report.sections.drift_analysis}
                       </p>
                       <div className="space-y-6">
                          <div className="space-y-2">
                             <div className="text-[9px] uppercase tracking-widest text-secondary/40">Architectural Note</div>
                             <p className="text-[11px] leading-relaxed text-secondary font-light">{report.sections.miryn_standout}</p>
                          </div>
                       </div>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
