---
name: motion-direction
description: Creates the motion system for a Corporate/Brochure site: interaction intent, trigger, duration, easing, allowed properties, responsive behavior, reduced-motion replacement, and performance risk. Use for animation, scroll choreography, hover response, transitions, and cinematic hero behavior.
---
# motion-direction

Write `motion-spec.json` after page composition and creative direction are approved. Every
interaction needs an id, user-facing intent, trigger, properties, duration, easing, reduced-motion
behavior and performance risk. Meaning may not depend on animation. Prefer opacity and transform;
pointer response updates CSS custom properties inside `requestAnimationFrame`.

Hero motion requires a static poster. Reduced motion means poster-only, visible content, no cinematic
autoplay, no scroll choreography, and no orbit animation. Seal the contract and request the
motion-accessibility reviewer before build approval.
