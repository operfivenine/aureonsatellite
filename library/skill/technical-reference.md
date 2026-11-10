# Technical reference and capabilities

[← For developers](../author-skill.md) · [Русский](technical-reference.ru.md)

**AURS Author Skill v0.7.0 · Early Beta (Frozen)**  
Target **Aureon 0.24.5 v420** · **AURS API 1.1**

## 1. Scope

The Skill supplies instructions, references and offline tools that help Codex design, write, validate and package a declarative audiovisual scene. It operates within the registered features of a specific SDK edition. Aureon loads the resulting `.aurs` package. The Skill runs on the authoring side and does not change the player.

For scoped edits, the Preserve workflow keeps unrelated systems intact and compares the original package against the result.

## 2. AURS package layout

An `.aurs` file is a ZIP container. The following layout illustrates possible files. Required paths and fields depend on the renderer and feature IDs.

~~~text
Theme.aurs
├── manifest.json             # ID, version, renderer, entry point and feature dependencies
├── scene.json                # Scene parameters, signals, behavior and resources
├── preview.png               # Rendered frame declared through scene.preview.v1
├── shaders/main.frag         # Fullscreen fragment shader where required
├── shaders/main.vert         # For compatible Mesh or Hybrid contracts
├── shaders/background.frag   # For compatible Hybrid contracts
├── shaders/mp_*.frag         # For supported multipass configurations
├── textures/...
└── meshes/...
~~~

See `api/docs/package.ru.md` and the applicable `sdk/docs/PACKAGE_RU.md` in the Skill archive. AURS does not execute arbitrary embedded Python. Keep asset generators outside the package.

## 3. Authoring architecture

### Stage A — Creative Direction

Choose workflow, art direction, resources, music and reference interpretation independently. Define the intended experience before choosing a technical implementation. Strict One-Shot preserves the first creative build.

### Stage B — Production Intelligence

Plan composition, depth, scale and how the world is constructed. Assign visible roles to meshes, material maps, light, atmosphere, reflections and local activity. Production One-Shot allows internal creative review and revision. Maximum resource intent follows SDK limits and the GPU budget.

### Stage C — Motion & Music Intelligence

Separate observer motion, autonomous world change and audio-driven events. Give attacks, sustained energy and decay distinct roles. For variable transport speed, integrate elapsed motion or phase instead of multiplying absolute time by instantaneous speed. Verify Reactive-First with real music.

### Stage D — Multi-Keyframe Engine

Identify corresponding objects, scales, materials and spatial relationships across ordered frames. Separate camera movement from world change. Design procedural transitions and inspect intermediate states. `aurs_keyframe_brief.py` checks the structure of the optional JSON sidecar. Image analysis and runtime features lie outside its scope.

### Stage E — Integration & Artistic Trials

Bring the authoring rules together while honoring the user's brief and the SDK. Evaluate packaging, SDK parsing, rendering, music, GPU performance and artistic quality separately. Stage E defines the CINE-01, PSY-01 and KEY-01 briefs.

## 4. Renderer and feature selection

Consult `sdk/FEATURE_REGISTRY.json`, `sdk/SCHEMA_FIELDS.json` and `api/reference/` in the archive. The docs cover Fullscreen Fragment, Mesh, Hybrid Mesh and documented extensions such as multipass, textures and reactive controls. Check each combination against its renderer. Use registered renderer IDs such as `scene.fullscreen_frag.v2`.

~~~powershell
cd aureon-aurs-author
py -3.13 -B scripts/aurs_lookup.py release
py -3.13 -B scripts/aurs_lookup.py renderers
py -3.13 -B scripts/aurs_lookup.py feature scene.preview.v1
py -3.13 -B scripts/aurs_lookup.py feature scene.multipass.experimental.v1 --renderer scene.fullscreen_frag.v2
py -3.13 -B scripts/aurs_lookup.py limits multipass
~~~

## 5. Authoring tools

| Tool | Purpose | Scope |
|---|---|---|
| `scripts/aurs_lookup.py` | Release, feature, GLSL symbol, channel and limit lookup | Read-only reference |
| `scripts/aurs_preflight.py` | Partial static checks of directories and archives | SDK parser check is separate |
| `scripts/aurs_pack.py` | Deterministic `.aurs` packaging | GLSL compilation is separate |
| `sdk/tools/validate_aurs.py` | Actual parser for the selected SDK | Rendering and GPU measurement are separate |
| `scripts/aurs_diff.py` | Compare packages or directories during scoped editing | Behavior requires separate verification |
| `scripts/aurs_diagnose.py` | Triage from symptoms and logs | Operates without starting the host |
| `scripts/aurs_audit.py` | Static resource and render graph audit | FPS and VRAM require measurement |
| `scripts/aurs_bench_compare.py` | Compare supplied GPU measurements | Requires measurements as inputs |
| `scripts/aurs_keyframe_brief.py` | Check the Multi-Keyframe JSON plan | Structure only |
| `scripts/aurs_trial_report.py` | Check trial report structure | Artistic acceptance requires review |
| `scripts/aurs_sync.py` | Replace auxiliary API documentation locally | Source acquisition and authentication are separate |

## 6. Delivery and evidence

Deliver one complete `.aurs`, a real render as `preview.png` when the target supports `scene.preview.v1`, and a short report. Include editable sources when requested or needed. Create video, GIF and contact sheets on request. Provide runtime evidence for `HOST_RENDER`, `REAL_MUSIC` and `GPU_PERFORMANCE` or mark the check `NOT_RUN`.

## 7. Early Beta limitation

In PSY-01, the user reviewed the full cycle and found the perceived movement and psychedelic intensity too weak. This trial failed artistic acceptance. It provides feedback about the authored result. SDK and API behavior have separate checks. The snapshot remains frozen until work resumes.

The archive includes `SKILL.md` and the Production Intelligence, Motion & Music and Multi-Keyframe references.
