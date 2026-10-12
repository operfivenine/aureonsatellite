# Aureon: System Requirements

[← Aureon](README.md) · [Русский](SYSTEM_REQUIREMENTS.ru.md)

## System requirements

| Component | Requirement / tested configuration |
| --- | --- |
| Architecture | Windows x64. ARM64 emulation has not been tested. |
| OS | Windows 11 24H2 / 25H2 tested, including IoT Enterprise LTSC 24H2. |
| Installer | Windows 10 build 19045 or later; application runtime on Windows 10 was not tested here. |
| OpenGL scenes | OpenGL 3.3 Core driver. Iris Xe, GTX 1050 and RTX 3070 tested. |
| QPainter scenes | Orbital Dawn and Warp use CPU rendering; their scene renderer does not require a dedicated GPU. |
| CPU / RAM | Minimum not measured. The lowest tested configuration is Core i5-7300HQ / 12 GB; this does not establish a 12 GB RAM requirement. |
| Graphics memory | Iris Xe shared memory and 2 / 8 GB discrete VRAM tested. |
| Components | Python and Qt are included in the Windows package; no separate Python installation is required. |

## Tested devices

| Device | CPU / RAM | GPU | Windows |
| --- | --- | --- | --- |
| HP OMEN | i5-7300HQ / 12 GB | GTX 1050 · 2 GB | IoT Enterprise LTSC 24H2 · 26100.9550 |
| MSI Evo E13 Flip | i7-1185G7 / 16 GB | Iris Xe · shared memory | 25H2 · 26200.9457 |
| Desktop | i5-13600KF / 32 GB | RTX 3070 · 8 GB | Pro 25H2 · 26200.9457 |

## Average draw rate of built-in GL scenes

Each GPU / scene row is the arithmetic mean of the available drawn-frames/s values in the run table. Missing values are excluded; quality and window size varied between runs. This summarizes observations rather than identical-settings benchmarks or diagnostic FPS.

| GPU | Scene | Average drawn frames/s |
| --- | --- | ---: |
| Iris Xe | Aureon Satellite | 13.7 |
| Iris Xe | Orbital Sun | 34.9 |
| Iris Xe | Stellar Horizon | 28.9 |
| Iris Xe | Storm Tornado | 14.9 |
| Iris Xe | Volcanic Valley | 5.7 |
| GTX 1050 | Aureon Satellite | 38.0 |
| GTX 1050 | Orbital Sun | 59.0 |
| GTX 1050 | Stellar Horizon | 53.8 |
| GTX 1050 | Storm Tornado | 36.3 |
| GTX 1050 | Volcanic Valley | 21.1 |
| RTX 3070 | Aureon Satellite | 62.4 |
| RTX 3070 | Orbital Sun | 62.6 |
| RTX 3070 | Stellar Horizon | 61.7 |
| RTX 3070 | Volcanic Valley | 62.7 |
