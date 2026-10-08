---
name: Tactile Clay Simulator
colors:
  surface: '#fcf8ff'
  surface-dim: '#dad6ff'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2ff'
  surface-container: '#efebff'
  surface-container-high: '#e9e5ff'
  surface-container-highest: '#e3dfff'
  on-surface: '#181445'
  on-surface-variant: '#484550'
  inverse-surface: '#2d2a5b'
  inverse-on-surface: '#f3eeff'
  outline: '#797581'
  outline-variant: '#cac4d2'
  surface-tint: '#64529f'
  primary: '#64529f'
  on-primary: '#ffffff'
  primary-container: '#b4a1f5'
  on-primary-container: '#46347f'
  inverse-primary: '#cdbdff'
  secondary: '#875138'
  on-secondary: '#ffffff'
  secondary-container: '#fdb697'
  on-secondary-container: '#79452d'
  tertiary: '#006b5b'
  on-tertiary: '#ffffff'
  tertiary-container: '#68bca9'
  on-tertiary-container: '#004a3f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e7deff'
  primary-fixed-dim: '#cdbdff'
  on-primary-fixed: '#1f0559'
  on-primary-fixed-variant: '#4c3a86'
  secondary-fixed: '#ffdbcd'
  secondary-fixed-dim: '#fdb697'
  on-secondary-fixed: '#351001'
  on-secondary-fixed-variant: '#6b3a23'
  tertiary-fixed: '#9ef2de'
  tertiary-fixed-dim: '#82d6c2'
  on-tertiary-fixed: '#00201a'
  on-tertiary-fixed-variant: '#005144'
  background: '#fcf8ff'
  on-background: '#181445'
  surface-variant: '#e3dfff'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.03em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '800'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 26px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 18px
  label-lg:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-md:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 14px
    letterSpacing: 0.06em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.375rem
  space-sm: 0.75rem
  space-md: 1.25rem
  space-lg: 2rem
  space-xl: 3rem
---

## Brand & Style

This design system blends **Claymorphism** and tactile 3D physical modeling with rigorous engineering workbench functionality. The aesthetic is inspired by physical modeling clay, pillowy matte volumes, and smooth injection-molded soft polymer finishes. It removes the sterile, flat monotony of traditional technical tools by introducing warmth, physical delight, and high haptic clarity.

The target audience encompasses creative technologists, simulation engineers, system builders, and educational creators who demand deep structural utility without clinical coldness. The emotional tone is friendly, reassuring, tactile, and curiously imaginative, anchored by high-contrast typographic hierarchy to ensure all analytical metrics, simulator graphs, and parameter inputs remain crystal clear.

## Colors

The palette grounds pastel clay hues with rich, deep-slate ink colors to maintain WCAG AAA/AA readability across complex dashboard surfaces:

- **Primary Clay (`#b4a1f5` - Soft Lilac / Lavender):** Used for primary container volumes, active tab cards, elevated focus frames, and top-level simulation groups.
- **Secondary Clay (`#ffb899` - Warm Peach):** Powers dynamic callouts, active state toggles, simulator running indicators, and high-priority parameter sliders.
- **Tertiary Clay (`#8fe3cf` - Soft Mint) & Accent Periwinkle (`#93c5fd`):** Applied to telemetry chips, status indicators, and sub-metric channels.
- **Surface Canvas (`#fdf8f6` - Tinted Cream / Warm Chalk):** Replaces harsh stark whites with a matte, non-glare canvas that makes inset clay highlights pop.
- **Neutral Foreground (`#1e1b4b` Deep Navy / Slate & `#312e81` Deep Indigo):** Delivers uncompromising contrast for numerical readouts, parameter keys, code strings, and critical telemetry values.

## Typography

The type system balances organic softness with technical exactness:

- **Headlines & Body (`Plus Jakarta Sans`):** Provides friendly, sculptured geometric roundedness matching the clay silhouette, while medium and bold weights preserve solid optical density on textured backgrounds.
- **Labels, Telemetry & Badges (`Space Grotesk`):** Provides crisp engineering structure for simulation readouts, unit metrics (e.g., `Hz`, `ms`, `kN`), code registers, and parameter controls. Its subtle mechanical quirks anchor the tactile elements into an instrument console feel.

## Layout & Spacing

Because claymorphic elements feature voluminous outer drop shadows and soft organic profiles, elements demand generous breathing room to avoid visual collision.

- **Grid Architecture:** Desktop simulator interfaces use a 12-column modular grid with generous 24px (`1.5rem`) gutters. Sidebars and tool drawers snap to fixed physical widths (280px-340px) while the canvas simulation plane is fluid.
- **Mobile Reflow:** Below 768px, multi-column simulation benches stack into a single column with collapsed 16px (`1rem`) gutters and outer canvas margins. Multi-knob tool trays reflow into horizontally scrolling pill carousels.
- **Element Pacing:** Component paddings use `space-md` (20px) to `space-lg` (32px) to let volumetric card rims and internal inset depths breathe comfortably around dense typography.

## Elevation & Depth

Claymorphic depth relies on **dual external shadows** paired with **dual internal inset highlights/lowlights**, simulating light hitting thick, soft-molded rubber or matte clay:

- **Base Clay Card Elevation:**
  - *Drop Shadow:* `12px 16px 32px -8px rgba(76, 59, 137, 0.16), -6px -6px 20px 0px rgba(255, 255, 255, 0.90)`
  - *Inner Clay Highlight:* `inset 4px 4px 8px 0px rgba(255, 255, 255, 0.65), inset -4px -4px 8px 0px rgba(76, 59, 137, 0.12)`
- **Embossed / Inset Wells (Input slots, sunken simulation wells, track trays):**
  - *Inverted Depth:* `inset 6px 6px 12px rgba(76, 59, 137, 0.18), inset -4px -4px 10px rgba(255, 255, 255, 0.85)`
  - *Outer Edge Rim:* `0 2px 4px rgba(255, 255, 255, 0.5)`
- **Hover & Pressed Haptics:**
  - Hover creates increased diffuse elevation: drop shadow blurs expand by 40% with an upward displacement of `-2px`.
  - Active press flattens the outer shadow and amplifies internal shadow opacity, imitating the compression of physical putty.

## Shapes

The design system exclusively adopts high-radius curvature (`roundedness: 3` / Pill-shaped) to reinforce the 3D molded clay impression:

- **Standard Containers & Modules:** 24px (`rounded-xl` to `rounded-2xl`) with squircle corner curvature.
- **Interactive Controls (Buttons, inputs, status pills, sliders):** Full pill border-radius (`9999px`).
- **Tactile Knobs & Indicators:** Pure circles (`50%` radius) with uniform 3D sphere bevels.
- **Rigid outlines are prohibited:** Borders must never use flat 1px solid outlines; perimeter definition is produced exclusively via clay-rim lighting and inner extrusion highlights.

## Components

### Buttons & Interactive Triggers
- **Primary Action (Lilac Clay):** Pill shape (`padding: 14px 28px`), lilac base (`#b4a1f5`), dark navy label (`#1e1b4b`), dual soft drop shadow, top-left white inset highlight. Pressing translates the button `+2px` downward and compresses the shadow stack into an embossed state.
- **Secondary Action (Peach Clay):** Warm peach base (`#ffb899`) with identical pill extrusion, reserved for simulator execution, toggles, or secondary triggers.
- **Ghost/Tertiary Action:** Molded chalk base (`#f1eef8`) blending seamlessly into background panels until hovered.

### Form Inputs & Telemetry Fields
- **Sunken Wells:** Text fields, number steppers, and formula inputs sit inside debossed "carved out" wells. The inner surface features a faint gradient with deep top-left drop shadows (`inset 4px 4px 8px rgba(76, 59, 137, 0.15)`).
- **Text:** High-contrast `#1e1b4b` monospace-friendly `Space Grotesk` typography for precision readouts.

### Chips & Embossed Badges
- **Status Pills:** Compact pill badges (height: 28px) with rounded caps, colored in mint (`#8fe3cf`), peach (`#ffb899`), or periwinkle (`#93c5fd`).
- **Simulation Indicators:** Raised clay bead dot (6px) on the left side of the chip that glows softly when a process is active.

### Cards & Modular Simulator Blocks
- **Multi-layer Clay Deck:** Top-level cards feature lilac or tinted-chalk volumetric bodies with 32px radii.
- **Nested Sub-Panels:** Child modules (e.g., parameter banks, curve monitors) appear either extruded outward (+4px clay relief) or carved inward (-3px debossed well), creating tangible hierarchical nesting without single divider lines.

### Switches, Knobs & Sliders
- **Pill Switch:** Elongated track sunk into the surface; the thumb knob is an ultra-plump circular clay bead that slides smoothly with elastic spring easing (`cubic-bezier(0.34, 1.56, 0.64, 1)`).
- **Engineering Slider:** Inset rail groove with an oversized tactile slider puck sporting two embossed grip ridges across its surface.