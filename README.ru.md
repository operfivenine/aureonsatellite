<p align="center">
  <img src="assets/readme/aureon-logo.png" alt="Aureon logo" width="210">
</p>

<h1 align="center">Aureon</h1>

<h3 align="center">Your personal music satellite.</h3>

<p align="center">
  <img src="assets/readme/badge-windows.svg" alt="Platform: Windows">
  <img src="assets/readme/badge-freeware.svg" alt="Distribution: Freeware">
</p>

<p align="center">
  <a href="https://github.com/operfivenine/aureonsatellite/releases/download/v0.22.3-v367/Aureon-0.22.3-v367-Setup-x64.exe"><img src="assets/readme/button-download.svg" alt="Download for Windows"></a>
  <a href="docs/user-guide.ru.md"><img src="assets/readme/button-guide.svg" alt="Read the user guide"></a>
  <a href="https://boosty.to/oper59"><img src="assets/readme/button-support.svg" alt="Support Aureon"></a>
</p>

<p align="center"><a href="https://ffmpeg.org/"><img src="assets/readme/badge-ffmpeg.svg" alt="Powered by FFmpeg / ffprobe"></a></p>

<p align="center"><a href="README.md">English</a> · <a href="README.ru.md">Русский</a></p>

**Aureon — бесплатный медиаплеер для Windows с музыкально-реактивными сценами, проекциями и минималистичным интерфейсом.** Слушайте музыку локально, смотрите видео, выбирайте сцену и создавайте своё пространство для прослушивания.

![Aureon со сценой Aureon Satellite](assets/readme/aureon-player.jpg)

## О приложении

Aureon объединяет воспроизведение и визуальные сцены. Создайте музыкальный плейлист, настройте оформление, включите полноэкранный режим или управляйте музыкой через мини-плеер в трее.

Приложение доступно бесплатно. Поддержка автора — по желанию.

## Скачать

**Aureon 0.22.3 · v367 · Windows x64**

**[Скачать установщик — 177.3 МиБ](https://github.com/operfivenine/aureonsatellite/releases/download/v0.22.3-v367/Aureon-0.22.3-v367-Setup-x64.exe)** · [Описание релиза](https://github.com/operfivenine/aureonsatellite/releases/tag/v0.22.3-v367)

Приложение уже установлено? Начните с [руководства пользователя](docs/user-guide.ru.md).

## Возможности

| Воспроизведение | Визуализация | Персонализация |
| --- | --- | --- |
| Локальная музыка и видео | 7 встроенных сцен | Цвета интерфейса |
| Очередь и поиск | Реакция на музыку | Classic / Transparent Glass |
| Shuffle и Repeat | Полноэкранный режим | Качество и сила реакции |
| Сохранение и импорт плейлистов | Отдельные проекции | Пользовательские AURS и AURP |
| Восстановление сессии | Спектральные визуализаторы | Трей и горячие клавиши |

## Визуальные сцены

<table>
<tr>
<td align="center" width="33%"><img width="220" src="assets/readme/satellite.jpg" alt="Aureon Satellite"><br><strong>Aureon Satellite</strong></td>
<td align="center" width="33%"><img width="220" src="assets/readme/sun.jpg" alt="Orbital Sun"><br><strong>Orbital Sun</strong></td>
<td align="center" width="33%"><img width="220" src="assets/readme/storm.jpg" alt="Storm Tornado"><br><strong>Storm Tornado</strong></td>
</tr>
<tr>
<td align="center"><img width="220" src="assets/readme/dawn.jpg" alt="Orbital Dawn"><br><strong>Orbital Dawn</strong></td>
<td align="center"><img width="220" src="assets/readme/stellar.jpg" alt="Stellar Horizon"><br><strong>Stellar Horizon</strong></td>
<td align="center"><img width="220" src="assets/readme/volcanic.jpg" alt="Volcanic Valley"><br><strong>Volcanic Valley</strong></td>
</tr>
</table>

В комплект также входит **Warp**. Нажмите название сцены внутри плеера, чтобы выбрать другую. [Посмотреть инструкцию →](docs/tutorials/03_Choose_Scene.ru.md)

## Библиотека AURS / AURP

Добавляйте в Aureon пользовательские визуальные сцены и отдельные проекции.

| Пакет | Что добавляет | Где импортировать |
| --- | --- | --- |
| **AURS** | Пользовательскую визуальную сцену | [Settings → Visuals → Import scene](docs/tutorials/19_Import_AURS_Scene.ru.md) |
| **AURP** | Пользовательскую проекцию | [Settings → Tray](docs/tutorials/20_Tray_Mini_Player.ru.md) |

**[Открыть библиотеку AURS / AURP →](library/README.ru.md)**

### Создать свою сцену или проекцию

**[API-библиотека для авторов (EN)](library/api/README.md)** описывает API стандартной библиотеки AURS **1.1**, пять технических starters и инструменты упаковки / проверки.

[Начать разработку (EN)](library/api/GETTING_STARTED.md) · [Справочник API (EN)](library/api/API_REFERENCE.md) · [Скачать комплект для авторов](library/aureon-authoring-api-en.zip)

## Системные требования

**Windows x64 · OpenGL 3.3 Core для GL-сцен · Python и Qt входят в Windows-комплект.**

| Компонент | Текущий ориентир |
| --- | --- |
| Windows | Проверены Windows 11 24H2 / 25H2, включая IoT Enterprise LTSC 24H2. Установщик принимает Windows 10 build 19045+; работа на Windows 10 здесь не проверялась. |
| Графика | Драйвер OpenGL 3.3 Core для пяти GL-сцен. Orbital Dawn и Warp используют QPainter. Проверены Iris Xe, GTX 1050 и RTX 3070. |
| CPU / ОЗУ | Минимум пока не измерен. **Core i5-7300HQ / 12 ГБ** — самая слабая проверенная конфигурация; это не требование «минимум 12 ГБ». |

### Проверено на трёх Windows-системах

| Система | CPU / ОЗУ | GPU | Windows | Ориентир FPS |
| --- | --- | --- | --- | --- |
| HP OMEN | i5-7300HQ / 12 ГБ | GTX 1050 · 2 ГБ | IoT Enterprise LTSC 24H2 · 26100.9550 | **До 60 FPS** |
| MSI Evo E13 Flip | i7-1185G7 / 16 ГБ | Iris Xe · общая память | 25H2 · 26200.9457 | **До 60 FPS** |
| Настольный ПК | i5-13600KF / 32 ГБ | RTX 3070 · 8 ГБ | Pro 25H2 · текущая сборка 26200.9457 | **60+ FPS** |

Условные ориентиры при подборе качества под устройство, а не средний результат всех сцен. Частота кадров зависит от сцены, настроек и размера окна; тяжёлые сцены могут работать заметно медленнее. Для RTX 3070 сопоставимые замеры дают около **61–63 нарисованных кадров/с**.

Начните с **Auto** и калибровки конкретной сцены. На слабом ПК режим **Lowest** снижает нагрузку визуализации.

**[Полные требования и замеры по сценам →](SYSTEM_REQUIREMENTS.ru.md)**

## Проверенные медиаформаты

**Проверено 79 образцов: 55 видео и 24 аудио.**

| Видеоконтейнер | Проверенные видеокодеки |
| --- | --- |
| **MP4 / M4V** | H.264, HEVC, AV1, MPEG-4 Part 2, VP9; M4V проверен с H.264 |
| **MKV** | H.264, HEVC, AV1, VP9, FFV1 |
| **WebM** | VP8, VP9, AV1 |
| **MOV** | H.264, ProRes, DNxHR, QuickTime Animation |
| **AVI** | MPEG-4 / Xvid, MSMPEG4v3, MJPEG, HuffYUV |
| **WMV / ASF** | WMV1, WMV2 |
| **MPEG / MPG** | MPEG-1, MPEG-2 |
| **TS / M2TS** | TS: H.264, HEVC, MPEG-2; M2TS: H.264 |

| Аудиофайл | Проверенные аудиокодеки |
| --- | --- |
| **MP3** | MP3 CBR / VBR |
| **FLAC** | FLAC 16 / 24-bit, до 192 кГц в проверенных образцах |
| **WAV** | PCM 16 / 24-bit, float32, PCM 5.1, MP3, IMA ADPCM |
| **M4A / AAC** | M4A: AAC-LC, ALAC, Opus; AAC: AAC-LC в ADTS |
| **OGG / OPUS** | OGG: Vorbis, FLAC; OPUS: Opus |

В составе соответствующих видеоконтейнеров также проверены: **AC3 / EAC3, DTS core, TrueHD, WMA2 и MP2**.

Среди проверенных 10-bit вариантов — H.264 High 10, HEVC Main 10, AV1 и VP9. Результаты относятся к конкретным сочетаниям кодека и контейнера.

**[Подробности и результаты аудита →](docs/media-formats.ru.md)**

## Первые шаги

1. Откройте очередь стрелкой справа, нажмите **+ FILES** и выберите музыку или видео.
2. Нажмите на трек в очереди, чтобы запустить воспроизведение.
3. Нажмите название сцены в плеере и выберите визуальный фон.
4. Нажмите **F11**, чтобы развернуть сцену на весь экран. Повторное нажатие вернёт плеер в окно.

<details>
<summary><strong>Показать, как добавить музыку</strong></summary>

![Добавление музыки](assets/readme/tutorials/01_Add_Music.gif)

[Пошаговая инструкция](docs/tutorials/01_Add_Music.ru.md)

</details>

<details>
<summary><strong>Показать, как выбрать сцену</strong></summary>

![Выбор сцены](assets/readme/tutorials/03_Choose_Scene.gif)

[Пошаговая инструкция](docs/tutorials/03_Choose_Scene.ru.md)

</details>

## Руководство пользователя

В руководстве — **14 разделов** с короткими записями настоящего интерфейса.

**Перетаскивание файлов:** добавьте музыку из Проводника; видео перетаскивайте **именно в очередь**. В смешанной очереди кнопка **«Показать видео сверху»** выводит видео в начало списка, сохраняя порядок воспроизведения.

| Хочу… | Инструкция |
| --- | --- |
| Добавить музыку или видео | [Музыка](docs/tutorials/01_Add_Music.ru.md) · [Видео](docs/tutorials/15_Play_Video.ru.md) |
| Организовать музыку | [Очередь и поиск](docs/tutorials/08_Queue_And_Search.ru.md) · [Плейлисты](docs/tutorials/22_Save_And_Import_Playlists.ru.md) |
| Выбрать визуальную сцену | [Scene Picker](docs/tutorials/03_Choose_Scene.ru.md) · [Сцена до воспроизведения](docs/tutorials/12_Idle_Scenes.ru.md) |
| Настроить графику | [Visual quality, Advanced и Calibrate Auto](docs/tutorials/26_Visual_Quality.ru.md) |
| Изменить оформление | [Цвета](docs/tutorials/02_Interface_Themes.ru.md) · [Стиль интерфейса](docs/tutorials/13_Interface_Style.ru.md) |
| Включить трей и проекции | [Режим трея](docs/tutorials/20_Tray_Mini_Player.ru.md) |
| Добавить собственную сцену | [Импорт AURS](docs/tutorials/19_Import_AURS_Scene.ru.md) |

**[Открыть руководство пользователя →](docs/user-guide.ru.md)**

## Частые вопросы

<details>
<summary><strong>Aureon бесплатный?</strong></summary>

Да. Приложением можно пользоваться бесплатно. Донаты добровольны.

</details>

<details>
<summary><strong>В Aureon есть стриминговый каталог музыки?</strong></summary>

Нет. Плеер воспроизводит ваши локальные файлы. Добавьте музыку или видео с компьютера в очередь.

</details>

<details>
<summary><strong>Можно установить пользовательские сцены?</strong></summary>

Да. Сцены **.aurs** импортируются из настроек Visuals, проекции **.aurp** — из настроек Tray.

</details>

<details>
<summary><strong>Aureon запоминает воспроизведение при закрытии?</strong></summary>

Восстановление сессии возвращает трек, очередь и позицию. Сохранение позиции регулируется через **Settings → Playback → Resume Playback**.

</details>

## Powered by FFmpeg / ffprobe

Aureon использует **[FFmpeg](https://ffmpeg.org/)** для обработки медиа и аудиоанализа, а **[ffprobe](https://ffmpeg.org/ffprobe.html)** — для информации о потоках. Спасибо участникам проекта FFmpeg.

## Обратная связь и поддержка

- [Новости в Twitter / X — @aureonsatellite](https://x.com/aureonsatellite).
- [Сообщить об ошибке](https://github.com/operfivenine/aureonsatellite/issues): укажите версии Aureon и Windows, шаги воспроизведения и приложите подходящий скриншот или лог.
- [Поддержать проект на Boosty](https://boosty.to/oper59).
- [Написать автору](mailto:aureonsatellite@gmail.com).

---

<p align="center"><strong>Ваша музыка. Своя орбита.</strong><br>Aureon — Your personal music satellite.</p>

