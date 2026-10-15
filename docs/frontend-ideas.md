# GitCanvas — Frontend Web App: Ideas & Architecture

> A modern, standalone frontend to replace/complement the Streamlit app at `gitcanvas-dm.streamlit.app/`

---

## 🗂️ Where Should It Live?

### Option A — `/web` folder inside the same repo ✅ *Recommended*
```
gitcanvas/
├── app.py            # existing Streamlit app
├── api/              # existing FastAPI backend
├── web/              # 👈 new Next.js / Vite frontend
│   ├── src/
│   ├── package.json
│   └── ...
```
**Pros:** One repo, shared contributors, same issues/PRs, great for open-source.  
**Cons:** Slightly more complex CI/CD (need to distinguish Python vs Node builds).

### Option B — Separate repo (`GitCanvas-Web`)
**Pros:** Cleaner separation of concerns, independent versioning.  
**Cons:** Context switching, PRs split across two repos, harder for contributors.

**Verdict:** `/web` inside this repo is the sweet spot for an open-source project.

---

## 🛠️ Tech Stack Recommendation

| Layer | Pick | Why |
|---|---|---|
| Framework | **Next.js 15 (App Router)** | SSR for SEO, API routes for proxying GitHub token, file-based routing, Vercel-native |
| UI Library | **shadcn/ui + Radix** | Accessible, composable, matches the dark/modern aesthetic |
| Styling | **Tailwind CSS v4** | Utility-first, pairs perfectly with shadcn |
| State | **Zustand** | Lightweight, no boilerplate, perfect for theme/username state |
| Data Fetching | **TanStack Query (React Query)** | Caching, background refresh, loading states |
| Animations | **Framer Motion** | Smooth tab transitions, card animations |
| Code Highlighting | **Shiki or react-syntax-highlighter** | Beautiful code copy blocks |
| Icons | **Lucide React** | Already used in shadcn ecosystem |

> **Quick alternative:** If you want something simpler to spin up fast — **Vite + React** with Tailwind and no SSR.

---

## 🎨 UI Vision & Design System

### Core Aesthetic
- **Dark-first** (GitHub-inspired deep navy/charcoal backgrounds)
- **Glassmorphism panels** for card preview areas
- **Accent:** Electric blue `#58a6ff` → violet gradient (similar to existing theme)
- **Font:** `Geist` or `Inter` for UI text, `JetBrains Mono` for code blocks

### Layout Pattern
```
┌──────────────────────────────────────────────────────┐
│  🎨 GitCanvas         [username input]   [⚡ Generate] │  ← Sticky top navbar
├──────────────────────────────────────────────────────┤
│  sidebar   │              main panel                  │
│            │   ┌─────────────────────────────────┐   │
│  Theme     │   │    LIVE SVG PREVIEW (glassmorphic)│  │
│  Colors    │   └─────────────────────────────────┘   │
│  Options   │   ┌─────────────────────────────────┐   │
│            │   │  📋 Code  │  one-click copy btn  │  │
│            │   └─────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 🧭 Pages & Routes

| Route | Description |
|---|---|
| `/` | Landing / hero page (why GitCanvas, showcase) |
| `/builder` | Main card builder app (replaces Streamlit) |
| `/builder/[card]` | Deep-linkable card routes (`/builder/stats`, `/builder/streak`) |
| `/themes` | Browse and preview all 15+ themes visually in a grid |
| `/docs` | API docs (lite) — how to use the badge URLs |
| `/roast` | Dedicated AI Roast page |

---

## 🧩 Key Features to Build (Priority Order)

### Phase 1 — Core Builder (MVP)
1. **Username input** with debounced GitHub fetch → show avatar + name below input as confirmation
2. **Card selector sidebar** — tabs for all 11 card types
3. **Theme picker** — visual color swatches, not just a dropdown
4. **Live SVG preview** — fetches from existing `gitcanvas-api.vercel.app` endpoints
5. **Code copy block** — toggle Markdown ↔ HTML, one-click copy with toast feedback
6. **SVG/PNG/JPEG download** — reuse the canvas trick from Streamlit

### Phase 2 — Design Enhancements  
7. **Theme Studio** — full color customizer with HEX/HSL pickers and gradient preview
8. **Multi-card Canvas** — drag-and-drop to arrange multiple cards into a README layout
9. **Side-by-side comparison** — pick 2 themes and compare output
10. **Theme Gallery** — `/themes` grid with hover preview

### Phase 3 — Smart Features
11. **AI Roast** tab with streaming text (use SSE or polling from Gemini)
12. **Profile Snapshot** — generate shareable link to your current config (store in URL params or localStorage)
13. **README Generator** — select a set of cards and get a full ready-to-paste README section
14. **GitHub Token in browser** — securely pass via Next.js API route (token never exposed in client URL)

---

## 🔌 API Strategy

The existing `gitcanvas-api.vercel.app` FastAPI backend already serves SVG via query params. The web frontend just needs to:

1. **Proxy requests through Next.js API routes** — so user tokens aren't exposed in browser URLs
2. **Add an `/api/github-profile` route** — fetch username data (avatar, name, bio) client-side to enrich the UI
3. Optionally **cache SVGs in browser** using TanStack Query

```
Browser → /api/proxy?card=stats&username=torvalds → gitcanvas-api.vercel.app/api/stats
```

---

## 🗓️ MVP Build Plan (Rough)

| Step | What | Est. Time |
|---|---|---|
| 1 | `npx create-next-app web/` inside repo | 15 min |
| 2 | Tailwind + shadcn setup | 30 min |
| 3 | Landing hero page | 2 hr |
| 4 | `/builder` layout with sidebar + main | 3 hr |
| 5 | Username input + GitHub profile fetch | 1 hr |
| 6 | Card tabs + theme picker | 3 hr |
| 7 | SVG preview + code copy | 2 hr |
| 8 | SVG/PNG download | 1 hr |
| **Total MVP** | | **~½ day** |

---

## 🌐 Deployment

- **Frontend:** Vercel (configured for `web/` subdirectory, or separate Vercel project)
- **Backend:** Already on Vercel (`gitcanvas-api.vercel.app`)
- **Streamlit:** Keep running at `gitcanvas-dm.streamlit.app` — don't kill it, redirect to the new app once stable

---

## 💡 Differentiators vs the Streamlit App

| Streamlit | Web App |
|---|---|
| Sidebar-only layout | Flexible multi-panel layout |
| Basic theme dropdown | Visual theme gallery with previews |
| No shareable state | Shareable URL with params |
| Slow first load (Python cold start) | Instant load (static assets) |
| Mobile-unfriendly | Fully responsive |
| Limited animations | Framer Motion, micro-interactions |
| No dark/light toggle for UI itself | Full dark/light UI mode |
| GitHub token visible in URL params | Token proxied server-side |

---

## 📦 Repo Structure After `/web` Addition

```
gitcanvas/
├── app.py                    # Streamlit app (keep)
├── api/                      # FastAPI backend (keep)
├── generators/               # SVG generators (keep)
├── themes/                   # Theme definitions (keep)
├── utils/                    # Utilities (keep)
├── web/                      # 👈 NEW
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx      # Landing
│   │   │   ├── builder/      # Main builder
│   │   │   ├── themes/       # Theme gallery
│   │   │   └── roast/        # AI Roast page
│   │   ├── components/
│   │   │   ├── CardPreview.tsx
│   │   │   ├── ThemePicker.tsx
│   │   │   ├── CodeBlock.tsx
│   │   │   └── ...
│   │   └── lib/
│   │       ├── github-api.ts
│   │       └── card-urls.ts
│   ├── public/
│   ├── package.json
│   └── next.config.ts
├── README.md                 # Update to mention web app
└── requirements.txt
```
