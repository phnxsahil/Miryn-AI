# Miryn Figma UI Kit — Design System & Components (v1.1)

This kit provides the atomic building blocks for Miryn, incorporating the "Void & Glass" aesthetic with high-specificity components.

---

## 1. Core Design Tokens

| Token | Value | Figma Usage |
|---|---|---|
| `bg-void` | `#030303` | Primary page background |
| `accent-purple` | `#c8b8ff` | Brand primary (buttons, focus, highlights) |
| `accent-glow` | `radial-gradient(var(--accent-purple) at 50%, transparent 100%)` | Backdrop glows (alpha: 15%) |
| `glass-fill` | `rgba(255, 255, 255, 0.035)` | Default card/bubble fill (20px blur) |
| `border-faint` | `1px solid rgba(255, 255, 255, 0.07)` | Default containment lines |
| `border-bright` | `1px solid rgba(200, 184, 255, 0.3)` | Selection/Active state border |

---

## 2. Specialized UI Patterns

### **A. Importance Dots**
- **Visual:** A row of 3-5 small circles (4px).
- **Style:** Filled dots use `accent-purple`, empty dots use `text-dim`.
- **Usage:** Memory cards to show the weight of a stored fact.

### **B. Confidence Meters & Score Bars**
- **Visual:** Horizontal track (2px height).
- **Track:** `rgba(255, 255, 255, 0.1)`.
- **Fill:** `accent-purple`.
- **Usage:** Identity traits (e.g., "Analytical: 85%").

### **C. The Streaming Cursor**
- **Visual:** A vertical block `▋`.
- **Animation:** 800ms blink cycle.
- **Color:** `accent-purple`.

---

## 3. Atomic Components (Specifics)

- **Input (Pill):** Height 48px, Radius 100px, `glass-fill`, `border-faint`. Focus: `border-bright` + subtle glow.
- **Button (Primary):** Pill shape, full `accent-purple` fill, Black text (Space Grotesk 600).
- **Button (Ghost):** No fill, white text, `border-faint`. Hover: `border-bright`.
- **Cards (Preset/Memory):** 12px radius, `glass-fill`. Selected: `border-bright` + `accent-glow` shadow.

---

## 4. Design Prompts

> **Prompt for Identity Visuals:**
> "Design a set of abstract, data-viz style components for an AI identity dashboard. Needs: 1. A confidence meter (thin purple progress bar on a dark track). 2. A stats card with a large mono-font number and a tiny purple growth arrow. 3. A timeline entry with a small mono date chip. Palette: #030303, #c8b8ff, and soft glass textures."
