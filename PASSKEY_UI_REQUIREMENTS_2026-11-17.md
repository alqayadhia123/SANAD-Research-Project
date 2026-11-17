# SANAD Passkey UI Requirements

Source basis: FIDO Alliance, *Passkey Icon Usage Guidelines* (August 2022).
Source document: `FIDO-Passkey_Icon_Usage_Guidelines-August2022.pdf`.
Scope: future SANAD passkey interface; these requirements do not mean Passkeys are currently implemented.

## Visual requirements

- Prefer the official vector SVG asset for digital UI; do not recreate or distort the mark.
- Minimum icon size: 24 × 24 CSS pixels, including the negative space already present in the supplied asset.
- Maintain surrounding free space at least as wide as the key in the icon.
- Use one flat color. Do not add gradients, textures, outlines, shadows, rotations, skew, stretching, or busy photo backgrounds.
- Maintain at least 3:1 contrast for the graphic against its background.
- Keep the FIDO passkey mark visually secondary to SANAD branding. Do not use it as the SANAD logo, app icon, or standalone product mark.

## Interaction and accessibility

- Interactive icon controls must have a touch target of at least 48 × 48 CSS pixels.
- Prefer a visible text label such as “Sign in with a passkey” or “Create a passkey”.
- When a visible label accompanies the icon, mark the icon `aria-hidden="true"` so screen readers do not announce redundant content.
- For icon-only controls, provide a descriptive `aria-label` and a `title` tooltip.
- Vertically center-align the icon with its text label.

## Copywriting

- Write “passkey” in lowercase except at the beginning of a sentence.
- Use cross-platform wording; do not imply that passkeys are specific to Apple, Google, Microsoft, or one operating system.
- Prefer “Sign in with a passkey”, “Create a passkey”, and “Supports passkey sign-ins”.

## Implementation gate

Do not display an active “Sign in with a passkey” or “Create a passkey” control until the underlying WebAuthn ceremony is implemented and tested. Until then, the interface may describe Passkeys as a planned capability but must not imply that authentication is available.