# Aureon: System Requirements

[← Aureon](README.ru.md) · [English](SYSTEM_REQUIREMENTS.md)

## Системные требования

| Компонент | Требования / проверенная конфигурация |
| --- | --- |
| Архитектура | Windows x64. ARM64-эмуляция не проверялась. |
| ОС | Проверены Windows 11 24H2 / 25H2, включая IoT Enterprise LTSC 24H2. |
| Установщик | Windows 10 build 19045 и новее; работа приложения на Windows 10 в этих тестах не проверялась. |
| OpenGL-сцены | Драйвер OpenGL 3.3 Core. Проверены Iris Xe, GTX 1050 и RTX 3070. |
| QPainter-сцены | Orbital Dawn и Warp используют CPU-отрисовку; дискретная видеокарта для рендера этих сцен не обязательна. |
| CPU / ОЗУ | Минимум пока не измерен. Самая слабая проверенная конфигурация — Core i5-7300HQ / 12 ГБ; это не требование «минимум 12 ГБ». |
| Графическая память | Проверены общая память Iris Xe и видеокарты с 2 / 8 ГБ VRAM. |
| Компоненты | Python и Qt входят в Windows-комплект; отдельно устанавливать Python не требуется. |

## Проверенные устройства

| Устройство | CPU / ОЗУ | GPU | Windows |
| --- | --- | --- | --- |
| HP OMEN | i5-7300HQ / 12 ГБ | GTX 1050 · 2 ГБ | IoT Enterprise LTSC 24H2 · 26100.9550 |
| MSI Evo E13 Flip | i7-1185G7 / 16 ГБ | Iris Xe · общая память | 25H2 · 26200.9457 |
| Настольный ПК | i5-13600KF / 32 ГБ | RTX 3070 · 8 ГБ | Pro 25H2 · 26200.9457 |

## Средняя частота рисования встроенных GL-сцен

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
