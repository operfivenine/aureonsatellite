# Portability and platform testing

[← API](../README.md) · [Русский](portability.ru.md)

Use one declarative scene contract across Windows, Linux and macOS. Keep exact filename case, portable relative paths with forward slashes, UTF-8 and declared resource types. Do not depend on `C:/`, backslashes, the current working directory or a particular installation path.

Do not import WinAPI, DWM, native DLLs or Python into an AURS. Player menus, window behavior, audio backends and platform adapters belong to Aureon. Report a reproducible host defect separately rather than embedding platform-specific application code in the package.

Test the actual target OS, architecture and GPU driver. Check import, resources, shader compilation, quality/AA, fullscreen, cameras, scene switching, audio response and restart. Record untested platforms honestly. Compatibility of a manifest feature is not proof of every shader's behavior on every driver.

When reporting an issue, include the package ID/version and hash, Aureon version, OS/architecture/GPU/driver, renderer, graphics settings, reproduction steps and the exact error. Share only relevant logs; remove private track paths or metadata that are not needed for reproduction.
