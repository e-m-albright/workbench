# Scroll-driven product storytelling

Read this reference only when the user asks for a scroll-driven narrative,
cinematic product presentation, or a fixed visual that transforms between page
sections. This pattern is often called **scrollytelling**.

## Preferred architecture

Use native document scrolling with a sticky visual stage. Avoid wheel-event
scroll-jacking unless the experience has an explicit, tested reason to replace
browser behavior.

```text
page
├── persistent navigation
├── sticky media stage
└── semantic content sections
    ├── hero
    ├── feature or material detail
    ├── technical metric
    └── closing state
```

- Content sections remain normal semantic HTML and define the narrative.
- The media stage is `position: sticky` or fixed within a bounded wrapper and is
  pointer-transparent unless it contains real controls.
- An `IntersectionObserver` can select discrete section states. Use normalized
  scroll progress only when the visual requires continuous interpolation.
- Keep one authoritative state model for media transforms and section copy.
  Avoid independent animation timelines that can drift apart.

## Choose the media primitive deliberately

| Primitive | Best for | Main constraint |
|---|---|---|
| Image sequence | Art-directed camera movement and predictable rendering | Many assets; preload and responsive sizing matter |
| Video scrub | Photorealistic motion from a rendered source | Seeking behavior and codec keyframes can stutter |
| CSS transforms | Simple translation, scale, rotation, and opacity | Cannot create convincing new camera angles |
| WebGL or 3D model | Interactive perspective, lighting, exploded views | Highest performance and implementation cost |

Do not reach for a live 3D scene when a rendered image sequence answers the
visual requirement. Prototype the media pipeline before building every section.

## State model

Define named keyframes rather than scattering magic scroll offsets:

```ts
type SceneState = {
  opacity: number;
  rotate: number;
  scale: number;
  x: number;
  y: number;
};

const scenes: SceneState[] = [
  { opacity: 1, rotate: -18, scale: 0.8, x: 24, y: 4 },
  { opacity: 1, rotate: 0, scale: 1, x: 18, y: 0 },
  { opacity: 1, rotate: 0, scale: 1.8, x: 12, y: -16 },
];
```

Map each section to a scene. Interpolate between adjacent scenes only when
continuous motion adds meaning. Text can enter and exit independently with
short opacity and translation transitions.

Framer Motion is sufficient for React state transitions and moderate scroll
interpolation. Use GSAP ScrollTrigger when the timeline, pinning, or sequencing
is too complex to express clearly with component state. Prefer existing project
dependencies over adding either library.

## Accessibility and fallback

- Respect `prefers-reduced-motion`. Show stable section artwork or crossfades and
  disable scrubbing, parallax, pulsing, and rapid camera movement.
- Preserve keyboard, Page Up/Down, spacebar, touch, and browser history behavior.
- Keep headings and explanatory copy in DOM order even when the visual stage is
  composited separately.
- Decorative media uses empty alt text. Meaningful state changes need equivalent
  text in the section.
- Do not require motion to understand a specification or call to action.

## Responsive behavior

Desktop can use a split layout with a sticky stage. On narrow screens, prefer one
of:

1. media above each section as a static or short transitioning frame
2. a shorter sticky region followed by normal content
3. an intentionally simplified image sequence

Recompose the scene instead of merely shrinking desktop coordinates. Test short
and tall mobile viewports, orientation changes, touch scrolling, and browser UI
that changes viewport height.

## Performance

- Set explicit media dimensions to prevent layout shift.
- Preload only the first scene and near-future frames; lazy-load the rest.
- Use responsive AVIF/WebP images and poster frames.
- Animate transform and opacity where possible.
- Keep scroll handlers passive and update visual state through
  `requestAnimationFrame`; avoid layout reads followed by writes on every event.
- Test on a mid-range mobile device with CPU and network throttling.
- Provide a readable experience before the heavy media finishes loading.

## Verification

Test the beginning, every section boundary, rapid scrolling, reverse scrolling,
refresh at a deep anchor, resize, reduced motion, keyboard navigation, and mobile
touch. Inspect visual continuity and measure Core Web Vitals. A polished desktop
capture is not evidence that the interaction works.

## Research seed

A common product sequence is: diagonal hero view, upright product view, macro
material crop, component detail, animated technical effect, diagnostic display,
and exploded final state. Treat these as art-direction keyframes, not a required
page template.
