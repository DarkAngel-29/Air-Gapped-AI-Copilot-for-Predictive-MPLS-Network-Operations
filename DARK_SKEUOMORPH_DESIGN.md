---
name: Tactile Skeuomorphic NOC
colors:
  surface: '#0f131c'
  surface-dim: '#0f131c'
  surface-bright: '#353943'
  surface-container-lowest: '#0a0e17'
  surface-container-low: '#181c25'
  surface-container: '#1c2029'
  surface-container-high: '#262a33'
  surface-container-highest: '#31353f'
  on-surface: '#dfe2ef'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#dfe2ef'
  inverse-on-surface: '#2c303a'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#ddb7ff'
  on-secondary: '#490080'
  secondary-container: '#6f00be'
  on-secondary-container: '#d6a9ff'
  tertiary: '#a8ffd2'
  on-tertiary: '#003824'
  tertiary-container: '#5be9ad'
  on-tertiary-container: '#006645'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#f0dbff'
  secondary-fixed-dim: '#ddb7ff'
  on-secondary-fixed: '#2c0051'
  on-secondary-fixed-variant: '#6900b3'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#0f131c'
  on-background: '#dfe2ef'
  surface-variant: '#31353f'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-lg:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.04em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.06em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.08em
  label-engraved:
    fontFamily: JetBrains Mono
    fontSize: 9px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.12em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system establishes a high-fidelity tactical environment designed for critical mission operators, defense engineers, and network architects operating in air-gapped environments. The visual language merges high-density Network Operations Center (NOC) telemetry with machined rackmount studio hardware. The experience evokes absolute structural precision, zero-latency feedback, and tactile certainty. 

The aesthetic philosophy is **Machined Tactile Skeuomorphism**:
- Surfaces emulate matte bead-blasted anodized aluminum, milled dark gunmetal chassis, and recessed panel cutouts.
- Physical affordances borrow heavily from high-end analog test gear and studio audio processors: knurled rotary encoders, stamped mechanical push switches, countersunk hex screws, deep laser-etched debossed labels, and back-lit jeweler-grade jewel LEDs.
- Telemetry reads with raw digital fidelity, balancing razor-sharp data streams against tangible, physically weighted hardware interfaces that eliminate operational fatigue during high-stress incident responses.

## Colors

The palette is tuned for high-contrast, zero-fatigue observation in subdued control room environments:

- **Chassis & Base Plates:**
  - `Base Obsidian Canvas`: `#0e1117` (Deep substrate chassis)
  - `Panel Sub-chassis`: `#131720` (Secondary faceplate surface)
  - `Milled Module Surface`: `#181d27` (Tactile card plates, cards, raised module panels)
  - `Milled Trims & Insets`: `#2a313d` (Chassis bevel highlights, switch wells)
  - `Hardware Edge Rim`: `#3c4453` (Top-edge specular metal catch light)

- **Chromatics & Operational Telemetry:**
  - `Phosphor Signal Cyan` (`#00e5ff`): Primary active telemetry, live packet flows, MPLS circuit traces, active indicators.
  - `Synaptic Copilot Violet` (`#a855f7`): Air-gapped neural model inference, root cause synthesis, predictive vector branches.
  - `Mil-Spec Green` (`#10b981`): Optimal link health, cryptographic lock integrity, converged routing states.
  - `Telemetry Warning Amber` (`#f59e0b`): High jitter, BGP route flapping, thermal threshold warnings.
  - `Fault Alert Ruby` (`#ef4444`): Interface down, fiber cut, buffer exhaustion, security perimeter trip.

- **Monochrome & Physical Engravings:**
  - `Laser-Etched Screened Text`: `#64748b` (Secondary labels, metric legends, scale ticks)
  - `Specular Face Text`: `#e2e8f0` (Primary metric readouts and switch states)
  - `Stamping Shadow`: `#000000` (Recessed shadow offsets)

## Typography

Typography functions as both mission telemetry display and physical panel labeling:

- **Panel Labels & Dial Markings (`label-engraved`, `label-sm`):** Rendered in uppercase **JetBrains Mono**. These emulate stamped, screen-printed, or laser-engraved metal faceplates with a simulated inset bevel: text shadow `0px 1px 0px rgba(255, 255, 255, 0.12)` coupled with top shadow `0px -1px 0px rgba(0, 0, 0, 0.8)`.
- **Telemetry Readouts & Stream Logs (`label-md`, `label-lg`):** Strict tabular figures (`tnum`) in **JetBrains Mono** guarantee stable data columns during multi-gigabit throughput shifts.
- **Hierarchical Panel Headers & Analysis Narrative (`Inter`):** Clean, crisp, neutral sans-serif ensures maximum legibility for incident retrospectives, topology descriptions, and AI synthesis narratives.

## Layout & Spacing

Layout mirrors an engineered modular rack chassis (standard 19-inch euro-rack architecture scaled to 4K NOC wall displays, operator monitors, and field tablets):

- **Grid Discipline:** A compact 12-column or 16-column layout with fixed 16px/24px inter-rack gutters. Modules behave as removable physical sub-chassis blades with structural separation lines.
- **Density Profile:** NOC operations require high information density. Internal module padding standardizes around `space-sm` (8px) and `space-md` (12px), keeping primary controls and metrics immediately actionable without excessive vertical scanning.
- **Reflow Hierarchy:** On multi-display setups, topology and AI copilot blades sit side-by-side in parallel 8-column configurations. On field displays, secondary controls stack cleanly into indexed hardware rack groups.

## Elevation & Depth

Visual depth is achieved through mechanical lighting models, directional specular highlights, and calibrated physical insets:

- **Light Source Geometry:** A uniform top-down virtual light angle (90 degrees overhead).
- **Physical Inset (Wells & Troughs):**
  - Used for LED sockets, recessed toggle track grooves, and slider paths.
  - Constructed via: `box-shadow: inset 0 2px 4px rgba(0,0,0,0.85), inset 0 1px 1px rgba(0,0,0,0.95), 0 1px 0 rgba(255,255,255,0.06);`.
- **Extruded Faceplates & Knobs (Raised Hardware):**
  - Buttons, rotary encoders, and card modules utilize two-tone milled bevels.
  - Top edge highlight: `1px solid rgba(255, 255, 255, 0.14)`.
  - Bottom edge shadow: `1px solid rgba(0, 0, 0, 0.7)`.
  - Ambient cast shadow: `0 4px 12px rgba(0, 0, 0, 0.6), 0 1px 3px rgba(0, 0, 0, 0.8)`.
- **Rotary Dial Knurling & Cylinders:** Circular concentric gradients (`radial-gradient` layered with repeating conic knurl ticks) cast an asymmetrical radial shadow to communicate physical rotation.
- **Photonic LED Glows:** Illuminated LEDs employ a hard center bead with soft multi-tier Gaussian bloom: `box-shadow: 0 0 4px #color, 0 0 12px #color, inset 0 1px 1px #fff`.

## Shapes

The form factor prioritizes milled, industrial geometry:

- **Tight Corner Radii:** Base components utilize tight `0.25rem` (4px) corner radii (`roundedness: 1`), simulating precision CNC-cut metal edges rather than consumer-soft curves.
- **Panel Chassis Enclosures:** Outer rack modules use a structured `0.5rem` (8px) curve with visible countersunk screw geometry placed in cardinal corners.
- **Radial Hardware Elements:** Encoders, status LEDs, and test ports strictly enforce 1:1 circular symmetry (`rounded-full`) with concentric milled bezels.

## Components

### Buttons & Mechanical Switches
- **Machined Pushbuttons:** Raised anodized blocks with metallic linear gradients (`#2a313d` to `#181d27`). Active/pressed state physically shifts 1px downward, swaps highlight/shadow rings, and illuminates a centered 2px rectangular phosphor LED slot.
- **Rocker Switches:** Dual-state switches seated in deep recessed troughs. When toggled, the active side displays an angled specular highlight and a sunken opposite pole.
- **Copilot Action Switch (Violet):** Features a specialized knurled rim and illuminated synaptic violet backlighting when AI telemetry automation is engaged.

### Rotary Encoders & Fine-Tune Knobs
- Rendered with layered concentric circles: an outer fixed bezel with engraved increment hash marks, a raised knurled grip ring, and a sunken center cap featuring a white or cyan radial position indicator pip.
- Hover displays high-precision readout overlays; scroll or drag rotates the indicator pip and adjusts numerical metric bands smoothly.

### Beveled LED Indicators
- Countersunk within circular micro-wells.
- State-driven:
  - `Offline/Unpowered`: Dull smoked glass socket (`#1a1f28`).
  - `Nominal/Healthy`: Mil-Spec Green `#10b981` core with a sharp specular center reflection.
  - `Warning`: Amber `#f59e0b` rapid-pulse ring.
  - `Critical`: Ruby Red `#ef4444` intense dual-stage flare.
  - `AI Copilot Active`: Neural Violet `#a855f7` breathing ambient halo.

### Input Fields & Terminal Consoles
- Sunken dark troughs (`#0e1117`) bordered by an inset shadow and a bottom metallic catch line. Text input utilizes `JetBrains Mono` with an amber or phosphor cyan block cursor.

### Telemetry Cards & Rackmount Trays
- Module containers styled as 1RU/2RU rack modules. Each chassis includes debossed hardware labels, an engraved serial ID bar, a status LED array, and top/bottom brushed aluminum edge separators.