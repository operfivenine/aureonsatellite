# Cameras and clocks

[← API](../README.md) · [Русский](cameras.ru.md)

Fullscreen v2 uses `behavior.camera`: shots, mode, transition/easing, limits, presets and optional manual control. Presets/manual require the corresponding features. Camera uniforms are typed and listed in the machine-readable reference. A custom shader may implement its own camera without declaring an unused standard rig.

`camera.transition=0` is allowed in fullscreen v2 only with required `scene.camera_cuts.experimental.v1`. It switches directly between prepared views. Ordinary nonzero transitions retain their previous behavior. In this profile, camera settings are inside `behavior`.

Mesh/Hybrid uses `camera.times`, `eyes`, `targets`, `fov`, `near`, `far` and `presets`. Additional `camera.clock` is Hybrid-only and requires `scene.mesh_camera_clock.experimental.v1`; values are route or scene. Without it, the previous route clock remains. With scene, Automatic uses the shared world clock; returning from a fixed view resumes the current phase instead of restarting the route.

The author defines route timing through `camera.times`. Camera.speed does not change the entire world's time. These clocks are not bound to media length or seek; pausing music does not necessarily stop independent world motion.

The host owns camera selection and menus. A package does not create a menu window or define application-button coordinates.
