# Aureon: System Requirements

[← Aureon](README.md) · [Русский](SYSTEM_REQUIREMENTS.ru.md)

## Tested systems

| System | CPU / RAM | GPU | OS / environment | Result |
| --- | --- | --- | --- | --- |
| HP OMEN | i5-7300HQ / 12 GB | GTX 1050 · 2 GB | Windows 11 IoT Enterprise LTSC 24H2 · 26100.9550 | Tested; up to 60 FPS |
| MSI Evo E13 Flip | i7-1185G7 / 16 GB | Iris Xe | Windows 11 25H2 · 26200.9457 | Tested; up to 60 FPS |
| Desktop | i5-13600KF / 32 GB | RTX 3070 · 8 GB | **Windows 11 26H2 · 26300.9711** | **Tests passed**; 60+ FPS |
| Linux · VM | — | VMware SVGA3D | Mint 22.3 Cinnamon / X11 · x86_64 | Tested |
| macOS · VM | Intel x86_64 | — | macOS · virtual machine | Tested |
| iMac · physical device | Intel Core i3 · 4 cores · 3.6 GHz / RAM — | Radeon Pro 555X | macOS · Intel | All tested AURS scenes render correctly |

## Average draw rate of built-in GL scenes

These are earlier Windows measurements; a fresh v385 run is not claimed.

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
