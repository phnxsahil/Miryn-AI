type WaveChartProps = {
  title: string;
  label: string;
  ticks: readonly string[];
  accent: string;
  variant: "memory" | "identity";
};

const paths = {
  memory: {
    line: "M24 40 C50 42 62 73 91 82 C119 91 126 61 153 67 C181 74 190 105 217 94 C246 82 251 69 277 79 C301 88 315 108 344 105",
    first: "M24 40 C50 42 62 73 91 82",
    rest: "M91 82 C119 91 126 61 153 67 C181 74 190 105 217 94 C246 82 251 69 277 79 C301 88 315 108 344 105",
    area: "M24 40 C50 42 62 73 91 82 C119 91 126 61 153 67 C181 74 190 105 217 94 C246 82 251 69 277 79 C301 88 315 108 344 105 L344 124 L24 124 Z",
  },
  identity: {
    line: "M24 73 C51 72 61 82 89 81 C116 80 122 67 150 70 C177 73 185 60 211 61 C239 62 247 41 272 35 C300 28 316 19 344 15",
    first: "M24 73 C51 72 61 82 89 81",
    rest: "M89 81 C116 80 122 67 150 70 C177 73 185 60 211 61 C239 62 247 41 272 35 C300 28 316 19 344 15",
    area: "M24 73 C51 72 61 82 89 81 C116 80 122 67 150 70 C177 73 185 60 211 61 C239 62 247 41 272 35 C300 28 316 19 344 15 L344 124 L24 124 Z",
  },
} as const;

export default function WaveChart({ title, label, ticks, accent, variant }: WaveChartProps) {
  const chart = paths[variant];
  return (
    <article className="wave-chart">
      <p className="text-sm text-[#A3A3A3]">{title}</p>
      <p className="mt-2 font-editorial text-2xl">{label}</p>
      <div className="wave-chart__frame">
        <div className="wave-chart__ticks">{ticks.map((tick) => <span key={tick}>{tick}</span>)}</div>
        <svg viewBox="0 0 370 148" role="img" aria-label={`${label} wave chart`} preserveAspectRatio="none">
          <defs>
            <linearGradient id={`wave-fill-${variant}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={accent} stopOpacity=".2" />
              <stop offset="1" stopColor={accent} stopOpacity="0" />
            </linearGradient>
          </defs>
          {[24, 88, 152, 216, 280, 344].map((x) => <line key={x} x1={x} y1="10" x2={x} y2="124" stroke="rgba(255,255,255,.075)" strokeWidth="1" />)}
          <path d={chart.area} fill={`url(#wave-fill-${variant})`} />
          <path className="wave-chart__line" d={chart.line} fill="none" stroke="rgba(255,255,255,.26)" strokeWidth="2" strokeLinecap="round" />
          <path className="wave-chart__line" d={chart.first} fill="none" stroke={accent} strokeWidth="2" strokeLinecap="round" />
          <path className="wave-chart__line" d={chart.rest} fill="none" stroke="rgba(255,255,255,.26)" strokeWidth="2" strokeLinecap="round" />
          <g className="wave-chart__pill" fill="rgba(255,255,255,.07)" stroke="rgba(255,255,255,.12)">
            <rect x="17" y="0" width="52" height="20" rx="10" />
            <rect x="301" y="0" width="52" height="20" rx="10" />
          </g>
          <g fill="rgba(255,255,255,.48)" fontSize="9" fontFamily="var(--font-ui)">
            <text x="43" y="13" textAnchor="middle">Week 1</text>
            <text x="327" y="13" textAnchor="middle">Week 4</text>
          </g>
        </svg>
      </div>
    </article>
  );
}
