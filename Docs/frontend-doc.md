# Chip Detector — Frontend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Routing](#routing)
6. [Pages](#pages)
7. [Components](#components)
8. [Theme System](#theme-system)
9. [Styling System](#styling-system)
10. [State Management](#state-management)
11. [Environment Variables](#environment-variables)
12. [Testing](#testing)
13. [Assets](#assets)

---

## Overview

Chip Detector is an AI-powered object detection web application. The frontend allows users to upload or select example images, choose a detection model, run inference, and view the predicted output. The UI supports **dark mode** (default) and **light mode**, switchable via a persistent toggle in the navbar. The selected theme is saved to `localStorage` and restored on every page load without any flash.

---

## Technology Stack

| Technology | Version | Why It Was Chosen |
|---|---|---|
| **Next.js** | 14.x | App Router enables Server Components, reducing JS sent to the browser. Built-in image optimisation (`next/image`), file-system routing, and TypeScript support out of the box. |
| **React** | 18.x | Industry-standard UI library. Concurrent rendering via React 18 provides smoother updates during inference. |
| **TypeScript** | 5.x | Catches prop-shape mismatches and API contract errors at compile time rather than at runtime. All components and interfaces are fully typed. |
| **Tailwind CSS** | 3.x | Utility-first CSS framework with `darkMode: "class"` strategy. Handles layout, transitions, and interactive states. Pixel-precise Figma values are applied via inline `style` props. |
| **Lucide React** | 0.378.x | Lightweight, tree-shakeable SVG icon set. Used for the Community nav link and password toggle. |
| **@iconify/react** | 6.x | Access to thousands of icon sets via a single component. Used for Solar icons on the detection page and nav icons. |
| **@iconify-json/solar** | 1.2.x | Offline Solar icon set data. Bundled locally so icons render without any external network request. |
| **Jest** | 29.x | Test runner configured with `next/jest` to understand Next.js internals (aliases, CSS modules, image mocks). |
| **React Testing Library** | 15.x | Tests UI from the user's perspective (queries by role, label, text) rather than implementation details. |

---

## Project Structure

```
frontend/
├── public/
│   └── images/                   # Static assets (logos, examples, thumbnail)
│       ├── chip-detector-logo.svg # Chip Detector logo mark
│       ├── login-illustration.png
│       ├── video-thumnail.png
│       └── example-1.png … example-4.png
│
├── src/
│   ├── app/                      # Next.js App Router (Server Components by default)
│   │   ├── layout.tsx            # Root layout — ThemeProvider wrapper, anti-FOUC script, metadata
│   │   ├── globals.css           # CSS custom properties (theme vars), base styles, utilities
│   │   ├── page.tsx              # Root route — redirects to /login
│   │   ├── login/
│   │   │   └── page.tsx          # Login page (Server Component + metadata)
│   │   ├── register/
│   │   │   └── page.tsx          # Register page
│   │   └── detection/
│   │       ├── page.tsx          # Detection page shell (Server Component)
│   │       └── DetectionClient.tsx  # Detection page logic (Client Component)
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   └── Navbar.tsx        # Top navigation bar with theme toggle button
│   │   ├── ui/                   # Primitive / atomic UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Card.tsx
│   │   ├── login/
│   │   │   ├── LoginForm.tsx     # Controlled form with validation
│   │   │   └── LoginScaleWrapper.tsx
│   │   ├── signup/
│   │   │   └── SignupForm.tsx
│   │   └── detection/            # Detection-page-specific components
│   │       ├── HowToUse.tsx      # Instructions panel + video thumbnail
│   │       ├── ModelSelector.tsx # Model radio-button group
│   │       ├── ImagePanel.tsx    # Input/output image drop zones
│   │       ├── ExampleImages.tsx # Clickable example image grid
│   │       └── ShareBar.tsx      # Social share + copy-link toolbar
│   │
│   ├── context/
│   │   └── ThemeContext.tsx      # Theme context, ThemeProvider, useTheme hook
│   │
│   ├── declarations.d.ts         # Global TypeScript declarations (CSS side-effect imports)
│   │
│   └── __tests__/
│       ├── DetectionPage.test.tsx
│       ├── LoginPage.test.tsx
│       ├── Navbar.test.tsx
│       └── UIComponents.test.tsx
│
├── .env.local                    # Local environment variables (gitignored)
├── .env.example                  # Committed template — documents all required variables
├── tailwind.config.ts            # Custom tokens, darkMode: "class"
├── next.config.mjs               # Next.js config (image remote patterns)
├── jest.config.ts                # Jest + next/jest integration
├── tsconfig.json                 # TypeScript path aliases (@/ → src/)
└── package.json
```

---

## Architecture

### Server Components vs Client Components

Next.js 14 App Router defaults every file in `app/` to a **Server Component** — runs only on the server, produces zero client JS. Any component that needs browser APIs (state, events, localStorage) is marked `"use client"`.

| File | Type | Reason |
|---|---|---|
| `app/layout.tsx` | Server | Static HTML shell; imports client `ThemeProvider` as a child |
| `app/login/page.tsx` | Server | Metadata export + static layout wrapper |
| `app/detection/page.tsx` | Server | Thin shell that imports `DetectionClient` |
| `context/ThemeContext.tsx` | Client | Reads/writes `localStorage`, mutates `document.documentElement` |
| `DetectionClient.tsx` | Client | Manages `useState` for model, images, and inference state |
| `Navbar.tsx` | Client | Uses `useTheme`, `@iconify/react`, and click events |
| `LoginForm.tsx` | Client | Controlled form with `useState`, `useRouter` |
| `ImagePanel.tsx` | Client | Drag-and-drop, file input ref, drag-over state |
| `ModelSelector.tsx` | Client | Click-to-select interaction |
| `ExampleImages.tsx` | Client | Click interaction |
| `ShareBar.tsx` | Client | Clipboard API (`navigator.clipboard`) |

### Data Flow on the Detection Page

```
DetectionClient (state owner)
│
├── ModelSelector        ← reads selectedModel, calls setSelectedModel
├── HowToUse             ← stateless, static content
├── ImagePanel (input)   ← reads inputImage, calls handleImageUpload
├── ImagePanel (output)  ← reads outputImage (read-only display)
├── [Infer button]       ← calls handleInfer (async inference stub)
└── ExampleImages        ← reads selectedExample, calls handleExampleSelect
```

All shared state lives in `DetectionClient`. Child components receive only what they need via props. No global store is required because state scope is limited to a single page.

### Inference Flow

1. User uploads a file → `handleImageUpload` creates a blob URL via `URL.createObjectURL` and stores it in `inputImage`. The previous blob URL is revoked to prevent memory leaks.
2. User selects an example → `handleExampleSelect` sets `inputImage` to the static `/images/example-N.png` path.
3. User clicks **Infer** → `handleInfer` sets `isInferring = true`, clears `outputImage`, calls the inference API (stub — replace `setTimeout` with `NEXT_PUBLIC_API_URL + NEXT_PUBLIC_INFER_PATH`), then sets `outputImage`.
4. `ImagePanel (output)` renders the result via `next/image` with `fill` + `object-contain`.

---

## Routing

| Route | Page Component | Description |
|---|---|---|
| `/` | `app/page.tsx` | Immediately redirects to `/login` |
| `/login` | `app/login/page.tsx` | Split-panel login screen |
| `/register` | `app/register/page.tsx` | Registration screen |
| `/detection` | `app/detection/page.tsx` | Main detection workspace |
| `/files` | _(planned)_ | File management |
| `/community` | _(planned)_ | Community hub |

Routing is handled entirely by the Next.js file-system App Router. No third-party router is used.

---

## Pages

### Login Page (`/login`)

A two-column full-viewport layout:

- **Left panel** — Chip Detector logo, "Precision Beyond Perception" tagline, and a decorative illustration (`login-illustration.png`).
- **Right panel** — A glassmorphism card containing `LoginForm` (`backdrop-filter: blur(18px)`, `rgba(255,255,255,0.12)` background).

`LoginForm` performs client-side validation (email regex, minimum 6-char password) before simulating an API call and routing to `/detection`.

### Detection Page (`/detection`)

The main workspace, divided into three vertical sections inside a 1164px centred column:

1. **HowToUse panel** — 400px tall themed card. Left: step-by-step instructions + "Watch Demo" gradient button. Right: `video-thumnail.png` with a circular play button overlay.

2. **Model selector + image panels** — `ModelSelector` renders three radio-style model buttons. Below it, two `ImagePanel` components sit side-by-side (input left, output right). Each has a floating blue badge label overlapping the top border.

3. **Infer button + example images** — A centred gradient button (456×76px) triggers inference. Below it, `ExampleImages` renders four 108×108px thumbnail buttons.

---

## Components

### `Navbar`

- Height: 100px. Background and shadow respond to the active theme via `var(--theme-navbar-bg)` and `var(--theme-navbar-shadow)`.
- Max-width 1440px centred, `justify-between` for logo ↔ nav links.
- **Logo** — renders the same transparent Chip Detector SVG logo in both themes.
- **Theme toggle button** — positioned between the Files link and Community button. Shows 🌙 in dark mode, ☀️ in light mode. In light mode the button itself turns `rgba(255,255,255,1)` (white) with a dark border; in dark mode it uses a translucent white background. Clicking calls `toggle()` from `useTheme`.
- Nav link text and icons inherit `color: var(--theme-text)` so they adapt automatically.

### `ImagePanel`

Handles input and output image zones via a single `variant` prop.

- Outer wrapper: `position: relative`, `paddingTop: 21px` — reserves space for the floating label badge.
- Label badge: `position: absolute; top: 0; left: 27px`. Figma-exact widths: `247.73px` (input), `352.09px` (output), height `42.43px`.
- Panel background and border use `var(--theme-card-bg)` and `var(--theme-card-border)`.
- Empty-state icons and placeholder text use `var(--theme-icon)` so they are readable in both themes.
- **Input variant**: click or keyboard Enter/Space opens a hidden `<input type="file">`. Drag-and-drop via `onDragOver`/`onDrop`.
- When an image is loaded, `next/image` renders it with `fill` + `object-contain`.

### `ModelSelector`

Three models as ARIA radio buttons (`role="radio"`, `aria-checked`). Selected state: logo-blue border `#079FF2` + blue tint background — unchanged across themes. Unselected state uses `var(--theme-model-btn-bg)`, `var(--theme-model-btn-border)`, and `var(--theme-text)`.

### `HowToUse`

Stateless. Text colours use `var(--theme-text)` (heading) and `var(--theme-text-dim)` (body). Video thumbnail border uses `var(--theme-card-border)`. Play button overlays via `position: relative; zIndex: 1`.

### `ExampleImages`

Four static examples as `role="option"` buttons inside a `role="listbox"`. Selected item gets the `example-selected` CSS class (cyan ring). The "Examples:" label uses `var(--theme-text)`.

### `ShareBar`

Facebook share, Twitter share, and copy-link actions. Clipboard API with 2-second "Copied!" feedback. Built with `lucide-react` icons.

### Primitive UI (`src/components/ui/`)

| Component | Description |
|---|---|
| `Button` | `forwardRef` button with four variants: `primary`, `secondary`, `ghost`, `infer`. Variant styles map to Tailwind class strings. |
| `Input` | `forwardRef` input with optional label, error message, and password visibility toggle (Eye/EyeOff). |
| `Card` | Generic card wrapper. |

---

## Theme System

### Overview

Chip Detector supports **dark mode** (default) and **light mode**, styled with the logo's bright and deep blues. The active theme is:

1. Stored in `localStorage` under the key `"theme"` (`"dark"` or `"light"`).
2. Reflected as the CSS class `light` on `<html>` (present in light mode, absent in dark mode).
3. Exposed to all components via the `useTheme()` React hook.

### Anti-FOUC Script

`app/layout.tsx` injects a tiny inline `<script>` in `<head>` that executes synchronously before the first paint:

```js
try {
  var t = localStorage.getItem('theme');
  if (t === 'light') document.documentElement.classList.add('light');
} catch(e) {}
```

This sets the correct HTML class before CSS variables are evaluated, preventing any flash of the wrong theme on reload.

### `ThemeContext` (`src/context/ThemeContext.tsx`)

```ts
// Public API
export function ThemeProvider({ children }: { children: React.ReactNode })
export function useTheme(): { theme: "dark" | "light"; toggle: () => void }
```

`ThemeProvider` wraps the entire app inside `layout.tsx`. On mount, `useEffect` reads `localStorage` and aligns React state with the class already set by the anti-FOUC script. Calling `toggle()` flips the state, persists to `localStorage`, and adds/removes the `light` class on `document.documentElement`.

### CSS Custom Properties

All themed values are CSS custom properties in `globals.css`. Dark mode defaults live in `:root`; light mode overrides live in `html.light`.

| Variable | Dark | Light | Used by |
|---|---|---|---|
| `--theme-bg` | `linear-gradient(#0D2033 → #06111D)` | `#F4FAFF` | `body` background |
| `--theme-navbar-bg` | `rgba(5,18,32,1)` | `rgba(255,255,255,1)` | `Navbar` header |
| `--theme-navbar-shadow` | `0px 4px 25px rgba(2,30,53,0.45)` | `0px 4px 25px rgba(0,0,0,0.08)` | `Navbar` header |
| `--theme-text` | `rgba(255,255,255,1)` | `rgba(33,33,33,1)` | All primary text |
| `--theme-text-dim` | `rgba(220,220,220,1)` | `rgba(80,80,80,1)` | Secondary / body text |
| `--theme-card-bg` | `rgba(7,159,242,0.10)` | `rgba(7,159,242,0.05)` | Glassmorphism cards |
| `--theme-card-border` | `rgba(7,159,242,0.30)` | `rgba(8,108,175,0.22)` | Glassmorphism borders |
| `--theme-model-btn-bg` | `rgba(7,159,242,0.05)` | `rgba(7,159,242,0.035)` | Model selector buttons |
| `--theme-model-btn-border` | `rgba(7,159,242,0.20)` | `rgba(8,108,175,0.18)` | Model selector borders |
| `--theme-icon` | `rgba(255,255,255,0.6)` | `rgba(33,33,33,0.5)` | Empty-state icons/text |
| `--theme-toggle-bg` | `rgba(255,255,255,0.08)` | `rgba(255,255,255,1)` | Toggle button fill |
| `--theme-toggle-border` | `rgba(255,255,255,0.18)` | `rgba(33,33,33,0.15)` | Toggle button border |
| `--theme-toggle-color` | `rgba(255,255,255,1)` | `rgba(33,33,33,1)` | Toggle button icon |

### Transitions

`globals.css` applies `transition: background-color 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease` to structural block elements and `transition: color 0.35s ease` to text elements. All themed properties animate smoothly when the `light` class is toggled.

### Logo

```tsx
src="/images/chip-detector-logo.svg"
```

The transparent SVG logo is used unchanged in both themes.

---

## Styling System

### Approach: CSS Variables + Tailwind Utilities + Inline Styles

- **CSS custom properties** drive all theme-sensitive colours (background, text, borders) defined in `globals.css`.
- **Tailwind utilities** handle layout (flexbox, gap, padding), transitions, and interactive states (hover, focus, disabled).
- **Inline `style` props** carry pixel-precise Figma values (exact widths, heights, border-radii) that would require one-off utility classes otherwise.

### Colour Palette

| Token | Dark | Light | Usage |
|---|---|---|---|
| `--theme-bg` | `#212121 → #000` gradient | `#ffffff` | Page background |
| `--theme-text` | `#ffffff` | `#212121` | Body text, labels |
| `#079FF2` | — | — | Logo bright blue (selected model, example ring) |
| `#086CAF` | — | — | Logo deep blue and label badge background |
| `btn-gradient` | `#079FF2 → #086CAF` | same | Infer, Watch Demo, Community, Login buttons |

### Glassmorphism Pattern

Used on the HowToUse panel, login card, and ImagePanel. Values use CSS variables so they adapt per theme:

```css
background: var(--theme-card-bg);
backdrop-filter: blur(16px);
-webkit-backdrop-filter: blur(16px);
border: 2px solid var(--theme-card-border);
box-shadow: 5px 10px 25px 0px rgba(0, 0, 0, 0.25);
border-radius: 20px;
```

### Infer Button Specification

| Property | Value |
|---|---|
| Width | 456px |
| Height | 76px |
| Border radius | 20px |
| Padding | 20px 200px |
| Alignment | `alignSelf: center` |
| Background | `linear-gradient(180deg, #079FF2 0%, #086CAF 100%)` |
| Font | Poppins SemiBold 24px, `line-height: 100%` |
| Text colour | `rgba(255,255,255,1)` (fixed — not theme-sensitive) |

### Typography

| Font | Weights | Usage |
|---|---|---|
| **Inter** | 400, 600, 700 | Headings, label badges, model selector, body text in detection |
| **Poppins** | 400, 500, 600 | Navbar links, form fields, Infer button, placeholder text |

### `btn-gradient` Class

Defined in `globals.css`. Applies `linear-gradient(180deg, #079FF2 0%, #086CAF 100%)` to the Infer button, Watch Demo button, Community nav link, and form submit buttons. The gradient is intentionally not theme-sensitive — it always renders the logo's blues.

### Custom Tailwind Tokens (`tailwind.config.ts`)

```ts
darkMode: "class",   // light class on <html> for light mode; absence = dark mode
colors: {
  brand: { cyan: "#079FF2", blue: "#086CAF" },
  surface: {
    DEFAULT: "#0d1117",
    card: "#1a2035",
    nav: "#131929",
    input: "#0d1420",
    panel: "#161e30",
  },
},
fontFamily: {
  sans: ["Inter", "ui-sans-serif", "system-ui"],
},
```

---

## State Management

No external library (Redux, Zustand, Jotai) is used. React's `useState`, `useRef`, and `useContext` cover all requirements.

| State | Location | Type | Purpose |
|---|---|---|---|
| `theme` | `ThemeContext` | `"dark" \| "light"` | Active colour theme; persisted to `localStorage` |
| `selectedModel` | `DetectionClient` | `ModelName` | Which DETR model is active |
| `inputImage` | `DetectionClient` | `string \| null` | Blob URL or static path of the input image |
| `outputImage` | `DetectionClient` | `string \| null` | Result image URL from inference |
| `selectedExample` | `DetectionClient` | `number \| null` | ID of the active example thumbnail |
| `isInferring` | `DetectionClient` | `boolean` | Disables Infer button during API call |
| `blobUrlRef` | `DetectionClient` | `useRef<string>` | Tracks last blob URL for revocation on next upload (prevents memory leaks) |
| `isDragOver` | `ImagePanel` | `boolean` | Visual feedback during file drag |
| `form` | `LoginForm` | `FormState` | Email + password field values |
| `errors` | `LoginForm` | `FormErrors` | Validation error messages |
| `isLoading` | `LoginForm` | `boolean` | Disables submit during API call |
| `showPassword` | `Input` | `boolean` | Toggles password field visibility |
| `copied` | `ShareBar` | `boolean` | 2-second "Copied!" feedback |

---

## Environment Variables

Defined in `frontend/.env.local` (gitignored). A committed template lives in `frontend/.env.example`.

| Variable | Example | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL — no trailing slash |
| `NEXT_PUBLIC_AUTH_LOGIN_PATH` | `/auth/login` | Login endpoint, relative to `NEXT_PUBLIC_API_URL` |
| `NEXT_PUBLIC_AUTH_REGISTER_PATH` | `/auth/register` | Register endpoint, relative to `NEXT_PUBLIC_API_URL` |
| `NEXT_PUBLIC_INFER_PATH` | `/infer` | Inference endpoint, relative to `NEXT_PUBLIC_API_URL` |

All variables use the `NEXT_PUBLIC_` prefix so they are available in client-side code. Server-only secrets must be added **without** this prefix.

To wire up real API calls, replace the `setTimeout` stubs in `LoginForm.tsx`, `SignupForm.tsx`, and `DetectionClient.tsx` with `fetch` calls to `process.env.NEXT_PUBLIC_API_URL + process.env.NEXT_PUBLIC_*_PATH`.

---

## Testing

Tests live in `src/__tests__/` and use **Jest** with **React Testing Library**.

### Configuration

- `jest.config.ts` uses `nextJest({ dir: "./" })` — handles Next.js path aliases, CSS module mocking, and environment setup automatically.
- `moduleNameMapper` maps `@/` → `src/`, CSS files → `identity-obj-proxy`, image files → `fileMock.ts`.
- `testEnvironment: "jsdom"` simulates a browser DOM.

### Test Files

| File | Covers |
|---|---|
| `DetectionPage.test.tsx` | `DetectionClient`, `ModelSelector`, `ImagePanel`, `HowToUse`, `ExampleImages` |
| `LoginPage.test.tsx` | `LoginForm` validation, submit flow, routing |
| `Navbar.test.tsx` | Link rendering, accessibility roles, theme toggle button presence |
| `UIComponents.test.tsx` | `Button` variants, `Input` label/error/password toggle |

### Testing Strategy

- Components are queried by ARIA role and label (`getByRole`, `getByLabelText`) — tests reflect user and screen-reader experience.
- Image files are mocked by `fileMock.ts` since `next/image` cannot render in jsdom.
- Inference flow: Infer button is disabled before an image is selected, enabled after.
- `ThemeProvider` depends on `localStorage` — mock with `jest.spyOn(Storage.prototype, 'getItem')` / `'setItem'` as needed.

---

## Assets

All static assets live in `frontend/public/images/`.

| File | Used In | Notes |
|---|---|---|
| `chip-detector-logo.svg` | Navbar, login page, registration page | Transparent blue Chip Detector logo mark |
| `login-illustration.png` | Login page left panel | Decorative 3D illustration |
| `video-thumnail.png` | HowToUse | Demo video poster image |
| `example-1.png` | ExampleImages | Clickable example input image |
| `example-2.png` | ExampleImages | Clickable example input image |
| `example-3.png` | ExampleImages | Clickable example input image |
| `example-4.png` | ExampleImages | Clickable example input image |

All images are rendered via `next/image` which automatically serves modern formats (WebP/AVIF), lazy-loads below-the-fold images, prevents layout shift, and optimises file size per viewport.

---

*Last updated: 2026-05-15*
