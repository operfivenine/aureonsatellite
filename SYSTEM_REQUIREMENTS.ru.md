# Aureon: System Requirements

[← Aureon](README.ru.md) · [English](SYSTEM_REQUIREMENTS.md)

## Проверенные системы

| System | CPU / ОЗУ | GPU | ОС / окружение | Результат |
| --- | --- | --- | --- | --- |
| HP OMEN | i5-7300HQ / 12 ГБ | GTX 1050 · 2 ГБ | Windows 11 IoT Enterprise LTSC 24H2 · 26100.9550 | Проверено; до 60 FPS¹ |
| MSI Evo E13 Flip | i7-1185G7 / 16 ГБ | Iris Xe | Windows 11 25H2 · 26200.9457 | Проверено; до 60 FPS¹ |
| Настольный ПК | i5-13600KF / 32 ГБ | RTX 3070 · 8 ГБ | **Windows 11 26H2 · 26300.9711** | **Тесты пройдены**; 60+ FPS¹ |
| Linux · VM | — | VMware SVGA3D | Mint 22.3 Cinnamon / X11 · x86_64 | 324 успешно, 15 пропусков; трей, мини-плеер, проекции и пакеты |
| macOS · VM | Intel x86_64 | — | macOS · виртуальная машина | Базовый набор: 324 успешно, 13 пропусков²; меню, DPR, запуск, подпись и DMG |
| iMac · реальное устройство | Intel Core i3 · 4 ядра · 3,6 ГГц / ОЗУ — | Radeon Pro 555X | macOS · Intel | Все проверенные AURS-темы отображаются корректно |

¹ Ориентиры FPS сохранены из прежних Windows-замеров; это не новые замеры v385 на 26H2. Для Linux/macOS FPS не указан. Прочерк означает, что сведения не предоставлены.

² После базового набора macOS проверялись изменения интерфейса и упаковки; полный набор повторно не запускался.

## Средняя частота рисования встроенных GL-сцен

Это прежние Windows-замеры; повторный прогон v385 не заявлен.

Для каждой пары GPU / сцена взято среднее арифметическое доступных значений «нарисованные кадры/с» из таблицы прогонов. Строки без этого значения пропущены; качество и размеры окна в прогонах различались. Это сводка наблюдений, а не сравнение при одинаковых настройках или FPS из диагностики.

| GPU | Сцена | Средние нарисованные кадры/с |
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
