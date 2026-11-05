# Scene release checklist

[← API](../README.md) · [Русский](release-checklist.ru.md)

| Check | Record |
| --- | --- |
| Identity | Own package ID, incremented three-part version, localized name with English fallback |
| Contract | Correct scene renderer, actual required features/capabilities, unchanged historical IDs |
| Container | Root manifest/scene JSON, permitted assets, exact case, UTF-8, no executables or path traversal |
| Import | New import and update in a separate test profile; retain the error text for failures |
| Native rendering | Shader compilation and first frame on each claimed GPU/OS |
| Quality | Low/Medium/High, declared Extreme, 50/100% resolution, AA and Advanced switches |
| Audio | Reactive v1/v2 as claimed; silence, quiet/loud passages, pause/resume, seek, rapid Next and repeat |
| Camera | Automatic and fixed views, transitions/cuts, return to Auto, fullscreen and resize |
| Resources | Scene switch away/back, restart, memory after repeated switches, history recovery |
| Track inputs | Palette transitions and title atlas, if used, including empty/long/Unicode titles |
| Delivery | Final package hash, Aureon version, tested OS/architecture/GPU, settings, results and known limitations |

Do not replace an untested row with a claim of universal support. Separate container acceptance, native rendering, performance measurement and artistic review. No player rebuild or automatic installation is required to publish a scene package.
