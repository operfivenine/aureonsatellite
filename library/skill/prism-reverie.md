# Prism Reverie — Development Case Study

[← For developers](../author-skill.md) · [Русский](prism-reverie.ru.md)

**AUREON / AURS · v0.1.0–v0.6.0**  
**Target:** Aureon 0.23.14 (build 399), AURS Standard Library API 1.1  
**Renderer:** `scene.fullscreen_frag.v2` (GLSL 330)  
**Status:** Historical development case study — not a single-prompt or one-shot success

## Overview

**Prism Reverie** is a music-reactive psychedelic scene created for the Aureon player using the AURS scene format. Its final direction combines a continuous flight into a central vanishing point, layered crystalline geometry, evolving kaleidoscopic compositions, brief near-white transitions, and musical events that alter how the space behaves.

The scene was developed through **six iterative versions**. It is a useful example of human-guided creative direction: the technical implementation evolved in response to precise feedback about *what the viewer should experience*, not simply how much geometry or shader complexity the scene contained.

The original goal was to approach the expressive intensity of classic MilkDrop-style visualizations while using a distinct procedural scene and AURS's native music-reactivity controls.

## Development timeline

| Version | Development focus | Result and feedback |
| --- | --- | --- |
| **0.1.0** | Five-way kaleidoscopic crystal composition with a 24-second autonomous sequence; basic low/mid/high response. | Geometry and movement were promising, but the scene felt detached from the music. It lacked forceful inward movement and psychedelic intensity. |
| **0.2.0** | Stronger bass-triggered forward motion, a twisting perspective, transient mid/high modulation, and a motion integrator. | Audio response improved; twisting was judged unsuitable for the original visual identity. |
| **0.3.0** | Restored the first crystal arrangement; replaced twist with a more direct bass-driven dive toward the central axis. | The camera impulse still did not create the desired sensation of continuous collapse into the center. |
| **0.4.0** | Tested a repeating volumetric tunnel mechanism based on a user-supplied GLSL reference. Continuous axial travel and rotation made layers emerge from depth and pass the camera. | The desired motion finally became clear, but the result was too close to the external technical reference. |
| **0.5.0** | Rebuilt the visual identity with original sevenfold crystalline sections, overlapping plates, and a procedural `glacier.png` material map. Separated bass drops, mid-frequency layer changes, and high-frequency glints. | Distinctive geometry and stronger audio causality, but the composition became comparatively repetitive. |
| **0.6.0** | Added a 16-second choreography with interlocking layers, unfolding formations, temporary near-white fields, and new light events. | Brought together recognizable crystalline materials, continuous inward travel, musical acceleration, and global changes to the visual composition. |

## Technical architecture of v0.6.0

The final package uses **AURS Fullscreen Fragment v2** with a GLSL fragment shader, an AURS `scene.json` signal graph, and a texture resource:

```text
scene/
├── manifest.json
├── scene.json
├── preview.png
├── shaders/
│   └── main.frag
└── textures/
    └── glacier.png
```

The `glacier.png` texture contributes material variation to the crystal surfaces. Quality profiles control the number of rendered ring layers: **5 on Low, 8 on Medium, and 11 on High**. These are parameters of the archived v0.6.0 build, not universal recommendations for AURS themes.

### Three cooperating systems

**1. Spatial travel.** An AURS integrator maintains continuous travel into the scene. A bass attack increases the travel rate, so a musical drop affects the viewer's apparent movement through depth rather than only surface brightness.

**2. Musical response.** AURS envelopes and audio features feed distinct controls:

| Musical source | AURS signal | Perceptual role |
| --- | --- | --- |
| Low-frequency attacks / beats | `bass_attack`, `bass_body`, `drop` | Short forward acceleration into depth |
| Mid-frequency energy / attacks | `layers` | Changes in plate arrangement and openness |
| High-frequency attacks | `spark`, `treble_flash` | Local glints and fast travelling flashes |

For example, the archived v0.6.0 travel-rate expression is:

```text
4.2 + 10.5 * drop * drop + 2.3 * unfold + 1.25 * white
```

The `drop` term links motion to music; `unfold` and `white` link it to the autonomous visual sequence. These are implementation values from this specific theme, not a general audio-reactivity formula.

**3. Autonomous visual choreography.** Three looping 16-second curves—`interlock`, `unfold`, and `white`—control large-scale compositional changes even in silence. The scene can tighten into overlapping crystal formations, open into a radial passage, approach a bright white field, and reveal a new configuration.

This separation matters: **music changes how events are experienced, while the world retains its own temporal identity**. The two systems cooperate without being reduced to the same animation.

## The creative turning points

### Motion must be perceptually clear

The early versions contained valid geometry, movement, and audio modulation, yet the intended feeling was missing. The decisive direction was concrete: *the image should continuously fall inward toward its center; new shapes should approach from depth, grow, and pass the camera*. That description proved more useful than a general request for a “more psychedelic” shader.

### The reference was a mechanism, not the final design

The v0.4 experiment used a **user-provided GLSL snippet referencing “Phantom Mode” by aiekick** ([Shadertoy reference](https://www.shadertoy.com/view/MtScWW)) to demonstrate repeated geometry, axial travel, and volumetric accumulation. The following version deliberately moved to a different sevenfold crystal construction and new material treatment. The external reference should still be acknowledged when documenting the development history; redistribution rights for any third-party source must be checked separately.

### Reactivity and choreography are different requirements

Version 0.5 demonstrated that bass-driven acceleration and differentiated frequency mapping can work technically while the scene still feels repetitive. Version 0.6 addressed that by introducing *large-scale changes in the scene's state* instead of merely adding more reactive detail.

### Strong first results and good iteration solve different problems

Prism Reverie is **not evidence that an AI authoring agent consistently creates exceptional scenes from one prompt**. It is evidence that detailed creative feedback, technical references, musical testing, and willingness to replace an ineffective approach can produce a stronger final result.

## Verification and boundaries

The archive contains the `.aurs` packages for all six versions, GLSL/scene source files, SDK preflight and validator results, and audio/GPU verification artifacts. The archived SDK validator reports success for all six packages targeting Aureon build 399 and AURS API 1.1. Those validator records also explicitly show `gpu_compilation: false`, so SDK-parser success must not be described as GPU compilation by itself.

The accompanying development reports describe additional host-render and music tests. In v0.2, the reported comparison found **19 strong bass events and corresponding dive responses** in a tested excerpt. These figures are historical developer-reported measurements, not independent proof of subjective visual quality.

The final artistic assessment was made through actual playback in Aureon. A technical PASS was never, by itself, sufficient to establish that the experience matched the intended psychedelic dynamics.

## What this taught the AURS Author Skill project

Prism Reverie subsequently served as a **case study** for the AURS Author Skill's Motion & Music Intelligence work. Its generalizable lessons are:

- **Describe the experience before prescribing algorithms.** Camera behavior, scene-state evolution, and musical causality should be understood together.
- **Separate attacks from sustained energy.** Bass kicks, ongoing low-frequency pressure, and release tails should not be treated as one interchangeable value.
- **Use music to affect spatial behavior.** Travel, openness, scale, topology, and light propagation can be more expressive than uniform brightness changes.
- **Preserve autonomous motion.** The scene should remain meaningful in silence without becoming independent of music during playback.
- **Evaluate perception, not just formulas.** A mathematically changing scene may look almost static; a technically complex signal graph may produce little audible-to-visual impact.
- **Allow changes of approach during iterative production.** Prism Reverie's largest gains came from changing the motion model and later the visual identity—not from merely tuning a few shader constants.

## Suggested reproduction exercise (new prompt, not the original historical prompt)

> Create an original AURS music-reactive psychedelic scene for Aureon. Build a strong spatial experience around an identifiable motion concept, and design a visual world that changes its composition over time. Use music to modify how the viewer moves through and perceives the scene. Distinguish low-frequency attacks, sustained mid-frequency motion, and short high-frequency events. Keep an autonomous visual cycle active in silence. Test the result with real music and inspect whether the intended effects are clearly visible. Do not copy Prism Reverie's crystal geometry, palette, numerical constants, or the third-party GLSL reference. Deliver one `.aurs` package with an embedded rendered preview and a concise technical report; do not generate extra videos unless requested.

## Project context

Prism Reverie was developed **before** the later AURS Author Skill v0.7.0 Early Beta modes were formalized. It is a retrospective example of **iterative creative direction**, not a benchmark proving Strict One-Shot or Production One-Shot behavior.

**Source material:** `Prism_Reverie_0_6_0.zip` (v0.1.0–v0.6.0 sources and verification artifacts) and the archived development conversation supplied by the project author.
