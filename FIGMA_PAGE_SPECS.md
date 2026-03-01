# Miryn Page Specs — Figma Site Map & Architecture (v1.1)

This document provides granular design specifications for every page in the Miryn application. All layouts use `#030303` as the void background and `#c8b8ff` (Purple) as the primary accent.

---

## 1. Public Pages (Landing & Auth)

### **A. Landing Page (The Mirror)**
*Layout: Vertical Scroll with Fade-in Animations.*
- **Hero:** "The Memory Layer." Large serif title. Subtitle: "We taught computers to speak. Now, we are teaching them to listen." CTA: [Initialize Access] [Sign in].
- **Sections 01-07:** As per `page.tsx` specs. Use thin `border-faint` lines to separate.
- **Color Accent:** Purple gradients behind key section headers.

### **B. Login / Signup**
- **Background:** `#030303` with a large `accent-glow` (Purple radial gradient) behind the central card.
- **Tagline:** Above card — "A quiet room for honest reflection." (EB Garamond italic).
- **Central Card:** `glass-fill`, centered.
- **Wordmark:** Top center, "Miryn" (Space Grotesk 600).
- **Inputs:** Pill radius, `glass-fill`, email + password.
- **CTA:** Primary purple button, full width.
- **Footer Link:** "Don't have an account? Sign up" below the card.

---

## 2. Core Application Pages (Post-Auth)

### **C. Onboarding Flow (The Mirror Calibration)**
- **Layout:** Full screen, no sidebar. Progress bar at top (Purple fill, glass track).
- **Steps:** 5 steps, max-width 640px, centered. Mono font step count (e.g., "01") top right.
- **Step 2 (Presets):** 3-column grid (desktop), 1-column (mobile). Cards use `glass-fill`.
- **Selection State:** `border-bright` + `accent-glow` box shadow (Purple).
- **Navigation:** Back button (Ghost, left), Next button (Purple, right).

### **D. Chat Interface (The Void)**
- **Sidebar (240px):**
  - "Miryn" wordmark.
  - [+] New conversation button (Purple border or fill).
  - List of conversations grouped by date.
  - Bottom: User Avatar + email + Settings icon.
- **Main Area:**
  - Header: Conversation title.
  - Message area: Full height scroll.
  - User bubbles: Right-aligned, `glass-fill`.
  - Miryn bubbles: Left-aligned, slightly different `glass-fill` or text-only on void.
  - Streaming Cursor: Blinking `▋` in Purple.
  - Input: Pill-shaped, `glass-fill`. Send button: Purple.
- **Empty State:**
  - Center: Large EB Garamond italic "A quiet room for honest reflection."
  - 3 suggestion chips below (Pill shapes, `glass-fill`).

---

## 3. Advanced Dashboard Pages

### **E. Identity Dashboard (The Core)**
- **Layout:** Max-width 1200px, centered.
- **Header:** Title + Version badge + Status badge (e.g., "v1.4.2" in mono, "Active" in Purple).
- **Stats Row:** 4 cards (Beliefs / Loops / Patterns / Emotions).
- **Two-Column Sections:**
  - Traits (Progress bars for scores).
  - Values (Progress bars for scores).
- **Full-Width Section (Beliefs):** List of beliefs with Confidence Meters (Purple).
- **Two-Column (Loops/Patterns):** Grid of cards detailing open loops and behavioral patterns.
- **Full-Width (Evolution Timeline):**
  - Entry: Date chip (mono) + description.
  - Example: "Miryn noticed your analytical trait strengthened..."

### **F. Memory Page (The Archive)**
- **Structure:** Three clear sections with headers.
- **Memory Card:**
  - Content: 2-line truncated text.
  - Bottom Row: Date + **Importance Dots** (Purple) + Forget button (Ghost, red hover).
- **Empty State:** Per section, EB Garamond italic text.

---

## 4. Systems & Settings

### **G. Settings Page**
- **Layout:** Two-column (Nav left, Content right).
- **Sections:** Account / Notifications / Privacy / Danger Zone.
- **Danger Zone:** 
  - Red-bordered card.
  - Content: Delete account info.
  - Interaction: Type "DELETE" into input to enable button.

### **H. Notification Centre**
- **Layout:** Slide-in 320px right panel.
- **Visuals:** Blur backdrop, Purple accent borders for unread items.

---
