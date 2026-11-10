# AURS Author Skill v0.7.0 Early Beta configuration

[← For developers](../author-skill.md) · [Русский](configuration.ru.md)

These settings are text instructions for Codex during authoring. Use human-readable values such as `Production One-Shot` or the canonical IDs below. All five axes are independent. An explicit creative brief takes precedence over presets. Aureon does not read these settings from a configuration file or the package JSON.

## 1. `workflow` — authoring process

| ID | Name | Creative revisions before first delivery | When to use |
|---|---|---|---|
| `adaptive` | Adaptive | Determined by the agent's chosen process | General tasks with no prescribed process |
| `strict_one_shot` | Strict One-Shot | None. Log technical fixes separately | Evaluate the first completed creative solution |
| `production_one_shot` | Production One-Shot | Allowed when they serve the brief | Deliver one polished result |
| `iterative` | Iterative / PASS | At stages agreed with the user | Track versions and preserve accepted decisions |

Production One-Shot produces one delivery and can include multiple internal drafts. Disclose internal revisions. Strict One-Shot preserves the first complete creative build for review. Record any technical repairs separately.

## 2. `art_direction` — creative strategy

| Value | Priority | Optional |
|---|---|---|
| `auto` | Choose based on the brief | A fixed template |
| `cinematic_environmental` | Composition, scale, structural logic, materials, light and environmental activity | World-scale morphing |
| `psychedelic_reactive` | Spatial sensation, psychedelic states, rhythm and musical causality | Crystal tunnels, symmetry or constant flashes |
| `transformative_procedural` | Coherent, visible changes in structures and their relationships | Destruction or a fixed number of phases |
| `hybrid` | Combine creative strategies where they serve the brief | Using every technique at once |

## 3. `resource_intent` — resource budget

| Value | Behavior |
|---|---|
| `balanced` (default) | Balance artistic quality against rendering cost |
| `efficient` | Keep the implementation compact while preserving the main creative goals |
| `maximum` | Allocate textures, meshes and passes by their visible contribution, without arbitrary quotas |
| `custom` | Follow user constraints such as platform, target resolution, measured GPU budget or packaging requirements |

Maximum allows a small archive, a single pass and any suitable renderer. Work within the documented SDK and the actual GPU budget. Measure FPS before reporting it.

## 4. `music_intent` — the role of music

| Value | Behavior |
|---|---|
| `adaptive` (default) | Choose the response that fits the brief |
| `reactive_first` | Let attacks, sustained energy and decay shape movement, events and transport |
| `ambient` | Use quiet or localized reaction. Minimal movement is valid |
| `custom` | Follow the user's specified rules for audio response |

Reactive-First allows different mappings for bass, mids and highs. The SDK has no universal BPM clock. Verify musical timing in Aureon using an actual track. Shader checks alone cannot establish sync.

## 5. `reference_mode` — visual inputs

| Value | Inputs | Interpretation |
|---|---|---|
| `none` | Brief only | Codex develops the visual language |
| `single` | One reference | Appearance, composition and style, with room for interpretation |
| `reference_set` | Independent references | Mood, objects, materials or viewpoints |
| `multi_keyframe` | Ordered images with optional timing | Temporal states of one world, with continuity and intermediate states |

Multi-Keyframe is a method for procedural transitions within one world. Multiple views of one station do not imply a change in topology. The optional `keyframe_intent.json` lives outside the package as an authoring aid. The runtime does not expose a `scene.multi_keyframe` feature.

## 6. Delivery and verification

Default delivery includes one `.aurs`, a real render embedded as `preview.png` where the target SDK supports `scene.preview.v1`, and a short report. Provide editable sources on request. MP4, GIF and contact sheets are optional deliverables. Report `STATIC_PREFLIGHT`, `SDK_PARSER`, `HOST_RENDER`, `REAL_MUSIC`, `GPU_PERFORMANCE` and `USER_ART` separately. Use `NOT_RUN` when a check could not be performed.

## 7. Example combinations

| Task | Workflow | Art direction | Resources | Music | References |
|---|---|---|---|---|---|
| Cinematic world | `production_one_shot` | `cinematic_environmental` | `maximum` | `ambient` / `adaptive` | `none` / `single` |
| Psychedelic audiovisual scene | `production_one_shot` | `psychedelic_reactive` | `maximum` | `reactive_first` | `none` |
| Transformation from references | `production_one_shot` | `transformative_procedural` | `maximum` | `adaptive` | `multi_keyframe` |
| First-attempt quality test | `strict_one_shot` | Any | Any | Any | Any |
| Scene revision | `iterative` | Match the scene | Per task | Per task | Per task |

Early Beta trial `PSY-01` failed artistic acceptance despite its technical complexity.

## 8. Minimal prompt

~~~text
$aureon-aurs-author
Workflow: Production One-Shot
Art Direction: Cinematic / Environmental
Production Budget: Maximum
Music Direction: Ambient
References: Single

Brief: [scene concept, focal image, mood and movement]
Delivery: one .aurs with a real preview.png and a brief report. No video.
~~~

Archive references include `references/CREATIVE_DIRECTION_ARCHITECTURE.md`, `references/CREATIVE_MODES.md` and `references/CREATIVE_DIRECTION_PROFILE_CARD_RU.md`.
