# Platform entry points and native interop

Source: [platform differences](https://kotlinlang.org/docs/multiplatform/compose-platform-specifics.html) and [UIKit interop](https://kotlinlang.org/docs/multiplatform/compose-uikit-integration.html).

Three seams:
1. native shell embeds a Compose screen/controller
2. Compose embeds a native view/controller
3. platform-native UI observes shared state

Keep seam code in the platform source set. Expose a small common composable/state/event API; do not leak UIKit/AWT/Android/DOM types into `commonMain`.

For native views hosted by Compose:
- `factory`: allocate/configure object and one-time delegate/listener wiring
- `update`: apply observable state idempotently; avoid unconditional expensive resets
- disposal/release: stop sessions, detach delegates/listeners/observers, release resources
- callback: update the single state owner without echo loops

Define modifier size/constraints, clipping, z-order/layers, transparency, accessibility semantics, focus/IME, gesture arbitration, threading, and lifecycle. Camera/map/web/native text views also own permission/session/error paths.

For Compose hosted by native UI, retain one controller/window owner and connect appearance/background/foreground/destruction to the appropriate lifecycle. Verify navigation bars, safe areas, rotation/resizing, keyboard, accessibility, and memory release.

Platform defaults intentionally vary: native text actions, scroll physics, back gestures, fonts, touch/mouse support, popups, and rendering. Prefer target-appropriate behavior over forced pixel identity.
