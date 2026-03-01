# Miryn — Design Toolkit

---

## Colors

| Token | Value | Role |
|---|---|---|
| `--bg-void` | `#030303` | Page background |
| `--bg-surface` | `#0a0a0a` | Elevated surfaces |
| `--bg-glass` | `rgba(255,255,255, 0.035)` | Glass fill |
| `--bg-glass-hover` | `rgba(255,255,255, 0.07)` | Glass fill on hover |
| `--text-white` | `#ffffff` | Primary text |
| `--text-off-white` | `#e0e0e0` | Secondary text |
| `--text-muted` | `#a0a0a0` | Supporting text |
| `--text-dim` | `#666666` | Placeholder / subtle text |
| `--text-ghost` | `#2a2a2a` | Inactive / scrollytelling resting state |
| `--accent` | `#c8b8ff` | Purple accent (primary action color) |
| `--accent-glow` | `rgba(200,184,255, 0.15)` | Glow halos |
| `--accent-dim` | `rgba(200,184,255, 0.4)` | Dimmed accent for borders/fills |

---

## Borders

| Token | Value | Use |
|---|---|---|
| `--border-faint` | `rgba(255,255,255, 0.07)` | Default card/container borders |
| `--border-hover` | `rgba(255,255,255, 0.15)` | Hovered border |
| `--border-bright` | `rgba(200,184,255, 0.3)` | Accent-hovered border |

---

## Typography

| Token | Stack | Use |
|---|---|---|
| `--font-display` | `'Space Grotesk', system-ui, sans-serif` | Headings, UI, body |
| `--font-serif` | `'EB Garamond', Georgia, serif` | Manifesto, subtitles, editorial |
| `--font-mono` | `'JetBrains Mono', monospace` | Labels, tags, badges, code |

### Type Scale

| Element | Size | Weight | Style |
|---|---|---|---|
| Hero title | `clamp(3.5rem, 9vw, 9rem)` | 600 | tracking `-0.05em`, line-height `0.95` |
| Mid-CTA title | `clamp(3rem, 8vw, 7rem)` | 700 | tracking `-0.05em`, line-height `0.95` |
| Hero subtitle | `clamp(1.1rem, 2vw, 1.8rem)` | 400 | serif italic |
| Mid-CTA tag | `clamp(1.2rem, 2vw, 2rem)` | 400 | serif italic |
| Manifesto line | `clamp(1.8rem, 3.5vw, 3.2rem)` | 400 | serif, line-height `1.45` |
| Card heading | `1.6rem` | 500 | tracking `-0.02em` |
| Timeline title | `2rem` | 500 | — |
| Body / card copy | `1rem` | 400 | line-height `1.7` |
| Tech desc | `0.9rem` | 400 | line-height `1.6` |
| Badge / label | `0.7rem` | 400 | mono, uppercase, tracking `0.15em` |

### Google Fonts Import

```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@300;400&display=swap" rel="stylesheet">
```

---

## Border Radius

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | `8px` | Small elements |
| `--radius-md` | `12px` | Cards |
| `--radius-pill` | `100px` | Buttons, chips, badges |

---

## Motion / Easing

| Token | Curve | Personality |
|---|---|---|
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Snappy, premium feel |
| `--ease-smooth` | `cubic-bezier(0.25, 0.46, 0.45, 0.94)` | Soft, natural transitions |

---

## Component Patterns

### Card

- Fill: `--bg-glass` → `--bg-glass-hover`
- Border: `--border-faint` → `--border-bright`
- Radius: `--radius-md`
- Hover: `translateY(-10px) scale(1.02)` + `box-shadow: 0 25px 60px rgba(0,0,0,0.6), 0 0 40px var(--accent-glow)`
- Top shimmer: `1px` gradient line `transparent → --accent-dim → transparent`

### Button / Nav CTA

- Fill: `--accent`, text `#000`
- Radius: `--radius-pill`
- Hover: `scale(1.05)` + `box-shadow: 0 0 30px var(--accent-glow)`

### Chip / Badge

- Fill: `--bg-glass`, border: `--border-faint`, radius: `--radius-pill`
- Font: `--font-mono`, `0.7rem`, uppercase, tracking `0.15em`

### Email Input Row

- Fill: `--bg-glass`, border: `--border-faint`, radius: `--radius-pill`
- Focus: border → `--accent-dim`, `box-shadow: 0 0 40px var(--accent-glow)`

---

## CSS Snippets

### Accent Gradient Text

```css
background: linear-gradient(135deg, var(--accent), #fff);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
background-clip: text;
```

### Ambient Glow Radial

```css
background: radial-gradient(circle, var(--accent-glow) 0%, transparent 70%);
```

### Selection Highlight

```css
::selection {
  background: var(--accent);
  color: #000;
}
```
