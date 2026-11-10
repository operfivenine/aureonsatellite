# AURS Author Skill

[← For developers](../author-skill.md) · [Русский](README.ru.md)

**v0.7.0 · Early Beta · Frozen**

A Codex workflow and toolset for creating, editing and checking `.aurs` scenes for Aureon.

The snapshot was frozen on 10 November 2026. Technical integration is complete and creative trials are partial. Artistic results require review. The Skill uses the existing AURS API.

**Target** — Aureon **0.24.5 v420** · **AURS API 1.1**.

## Capabilities

| Component | What it does |
|---|---|
| Creative Direction (A) | Selects workflow, art direction, resource budget, music intent and reference interpretation |
| Production Intelligence (B) | Plans cinematic worlds, composition, architecture, details, materials, lighting and review |
| Motion & Music (C) | Designs spatial movement, autonomous choreography and reactions to attacks, energy and decay |
| Multi-Keyframe (D) | Plans one procedural world from two or more ordered references |
| Integration & Trials (E) | Provides verification tools, separate acceptance gates and three test briefs |
| SDK and tools | Looks up feature IDs and GLSL symbols, checks and packages scenes, runs SDK parsing, and supports diagnosis, diffs and static audits |

The Skill guides the authoring agent. The player uses its existing format support. Image-based 3D reconstruction and new runtime fields lie outside the Skill's scope.

## Quick start

1. Open the Skill's `aureon-aurs-author/` directory and read `SKILL.md` and `CODEX_START_HERE_RU.md`.
2. Register the folder as a Skill in Codex or provide the complete archive or working directory and point Codex at `SKILL.md`. The Skills directory depends on your client.
3. If the Skill is registered as `aureon-aurs-author`, start the prompt with `$aureon-aurs-author`.
4. Specify the creative goal, profile, and any references or music.
5. Request one `.aurs` with a real embedded preview where the SDK supports it, plus a short report. Video and GIF are optional.

~~~text
$aureon-aurs-author
Workflow: Production One-Shot
Art Direction: Cinematic / Environmental
Production Budget: Maximum
Music Direction: Ambient
References: None

Create an original cinematic world with architecture at a monumental scale,
a strong composition, expressive materials and a living atmosphere.
Plan the world before selecting a renderer. Review the creative result internally.
Deliver one .aurs with an embedded preview and a short technical report.
No MP4, GIF or contact sheets.
~~~

Production One-Shot allows internal creative repairs before one delivery. Strict One-Shot preserves the first completed creative build and records any technical fixes separately.

## Profile settings

Set these five independent axes in the prompt, outside `manifest.json` and `scene.json`.

| Key | Values | Purpose |
|---|---|---|
| `workflow` | `adaptive` · `strict_one_shot` · `production_one_shot` · `iterative` | Internal revision and review cadence |
| `art_direction` | `auto` · `cinematic_environmental` · `psychedelic_reactive` · `transformative_procedural` · `hybrid` | Artistic goal |
| `resource_intent` | `balanced` · `efficient` · `maximum` · `custom` | Geometry, textures, passes and GPU budget |
| `music_intent` | `adaptive` · `reactive_first` · `ambient` · `custom` | Music's role in spatial behavior |
| `reference_mode` | `none` · `single` · `reference_set` · `multi_keyframe` | Interpretation of images |

## Documentation

- [Technical reference](technical-reference.md)
- [Configuration and profiles](configuration.md)
- The source guide also refers to installation and CLI, verification and limitations, directory architecture, prompt examples, and a publication checklist. These are additional source materials beyond the three supplied guides.

## Verification and Early Beta

The frozen Stage E report records **137 of 137 document and structure regression checks passing**. New scenes require separate visual review.

- **PSY-01 Synaptic Maelstrom:** package created. Artistic acceptance failed after the user reviewed the full cycle and found the motion and psychedelic intensity too weak.
- **CINE-01 Stormglass Shipyard:** `NOT_RUN`.
- **KEY-01 Eidolon Greenhouse:** `NOT_RUN`.

SDK parsing, rendering in Aureon, real-music playback, GPU measurement and artistic acceptance each require their own evidence.

## Compatibility and limits

Check the SDK edition and feature registries before targeting Linux, macOS or older Aureon builds. Multi-Keyframe is an authoring method.

The original snapshot includes SDK source, graphic assets and examples. The supplied README records no license file in the frozen Skill and calls for checking redistribution rights and selecting a license before publishing its full tree.

## Source layout

~~~text
.
├── README.md
├── docs/                    # Technical guides
├── prompts/                 # Codex prompts
├── aureon-aurs-author/      # Original Early Beta Skill
└── PUBLICATION_CHECKLIST_RU.md
~~~

The supplied source guide identifies the snapshot as `Aureon_AURS_Author_Skill_v0.7.0_Early_Beta_FROZEN_v399.zip` with SHA-256 `27e607be95db6510d98e0c7f5ce8ea5567bb49b0d0626f94543d108d3cf9df49`.
