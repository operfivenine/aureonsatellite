# Aureon WIN12 + FIX10: проверка форматов и кодеков

Проверено 11 октября 2026: **79 образцов, 55 видео и 24 аудио**.
Все образцы декодируются со звуком; все видеопотоки выдают меняющиеся изображения.
Aureon принимает 72 образца; 7 дополнительных расширений блокируются входным
фильтром приложения. Полный сценарий старт → пауза → продолжение → seek → конец
прошёл для 67 принимаемых образцов.
Четыре TS/M2TS имеют отдельное ограничение seek, один OGG с видео скрывается
из-за классификации расширения как аудио. Это не означает отсутствие декодера.

## Метод и среда

Проверены исходники принятой базы FIX10, полный PlayerWindow и его штатный
QMediaPlayer/QVideoWidget. Пользовательский установленный EXE отдельно не запускался.
Windows 11 10.0.26200, Python 3.13.1, PySide6/Qt 6.11.2, OpenCV 5.0.0,
PyAV 18.1.0; тестовый ПК RTX 3070. Активный Qt backend сообщил FFmpeg 7.1.5.
Отдельный ffmpeg.exe использован только для создания образцов, ffprobe.exe —
для подтверждения фактических потоков. Наличие encoder в ffmpeg.exe не принималось
за доказательство поддержки воспроизведения Qt.

Видео: 960×540, 24 FPS, обычно 3 секунды; контрольные TS — 6 секунд.
Аудио: тестовый синус, преимущественно stereo 48 кГц; дополнительно mono 44,1 кГц,
FLAC 96/192 кГц и шестиканальный WAV. Звук на устройстве выключен.
Получение валидных ненулевых аудиобуферов подтверждено QAudioBufferOutput.
Видеокадры проверены по размерам, временным меткам и разным хешам изображений.
Проверены загрузка, движение позиции, пауза без дрейфа, продолжение, перемотка
на 2 секунды и EndOfMedia. Отдельно OpenCV читает первый кадр и кадр после seek,
поскольку этот декодер используется Aureon для точного покадрового режима.
Оба чтения OpenCV прошли для 54 из 55 видеопримеров.
У BDAV M2TS с единственным ключевым кадром первый кадр читается, а после seek
кадр не получен. Обычное последовательное воспроизведение этого файла работает.

Тесты прошли на отдельном невидимом Windows desktop, с отдельными QSettings
и каталогом данных. Пользовательские настройки и исходники приложения не менялись.
Файлы FIX10, неизменённые файлы FIX09 и оконный модуль FIX08 проверены побайтово.

## Подтверждённые сочетания

| Контейнер / расширение | Фактически проверенные видеопотоки | Аудиопотоки в этих образцах |
|---|---|---|
| MP4 | H.264 Baseline/High/High 10/High 4:4:4; HEVC Main/Main 10; AV1 8/10-bit; MPEG-4 Part 2; VP9 | AAC-LC, Opus |
| MKV | H.264; HEVC Main/Main 10 и 4:4:4; AV1; VP9; FFV1 | AAC-LC, AC3, EAC3, DTS core, TrueHD, FLAC |
| AVI | MPEG-4 Part 2 / Xvid, MSMPEG4v3, MJPEG, HuffYUV | MP3 |
| MOV | H.264, ProRes Standard, DNxHR LB, QuickTime Animation | AAC-LC, PCM |
| WebM | VP8, VP9 8/10-bit, AV1 | Vorbis, Opus |
| M4V (контейнер MP4) | H.264 | AAC-LC |
| WMV/ASF | WMV1, WMV2 | WMA2 |
| MPEG/MPG | MPEG-1, MPEG-2 | MP2 |
| TS | H.264, HEVC, MPEG-2 | AAC-LC, AC3, MP2 |
| M2TS, включая BDAV | H.264 | AC3 |

| Аудиорасширение | Проверено |
|---|---|
| MP3 | CBR/VBR, stereo 48 кГц, mono 44,1 кГц |
| FLAC | 16/24-bit; 48/96/192 кГц |
| WAV | PCM 16/24-bit, float32, PCM 5.1, MP3, IMA ADPCM |
| OGG | Vorbis, FLAC |
| OPUS | Opus |
| M4A | AAC-LC, ALAC, Opus |
| AAC | AAC-LC в ADTS |

Аудиоанализ музыкальных образцов в Aureon завершился со state=ok.
Шестиканальный WAV дал шесть каналов декодированного PCM. Это проверка
декодирования, а не проверка 5.1 акустики или битстрим-передачи на ресивер.

## Выявленные ограничения

1. **Перемотка H.264 в TS/M2TS зависит от образца.** В четырёх файлах с единственным
   ключевым кадром в начале после перехода на 2 секунды звук продолжался,
   но новые видеокадры не приходили. Без seek эти же файлы воспроизводятся
   до конца с 72/144 кадрами. Контрольные файлы с ключевым кадром раз в секунду
   перематываются нормально. Спорные случаи и исправный контроль воспроизведены
   напрямую в отдельном QMediaPlayer/QVideoSink без обработчиков Aureon.
   Связь с GOP подтверждается сравнением образцов; внутреннюю причину в FFmpeg/Qt
   здесь не устанавливаем. Менять оконный код или графический рендер для этого
   оснований нет.

2. **WMA, AC3, AIFF, WV, OGV, FLV и 3GP не принимаются входным фильтром Aureon.**
   Их аудио/видеопотоки декодируются текущим Qt backend. Для WMA/AC3/AIFF/WV/FLV/3GP
   прошёл и полный транспортный сценарий напрямую в Qt. Для OGV дошли до конца
   кадры и позиция, но сигнал EndOfMedia не пришёл в пределах 4,5 секунды после seek.
   Регистрация дополнительных расширений сама по себе не добавляет декодер;
   в данном случае нужные декодеры уже показали работоспособность.

3. **OGG с Theora-видео Aureon считает аудиофайлом.** Qt декодирует кадры и Vorbis,
   но video_widget скрыт: media_kind определяется расширением. Этот случай
   требует классификации по фактическим потокам, если нужна поддержка OGG-видео.
   У него также не пришёл EndOfMedia; аналогичная особенность есть у OGV напрямую
   в Qt. Обычные OGG Vorbis/FLAC работают штатно.

## Границы проверки

Результаты относятся к указанным сочетаниям и текущему runtime. Все варианты
профилей/контейнеров и повреждённые файлы не перебирались. Не проверены WMV3/VC-1,
HE-AAC, DTS-HD MA, Dolby Vision, DRM, дисковые меню, сетевые потоки и passthrough.
HEVC Main 10 с BT.2020/PQ метаданными декодируется; образец не подтверждает
правильность HDR-цвета или тонмаппинга. Высокие разрешения, битрейты, 60 FPS
и аппаратное ускорение на GTX 1050/Intel отдельно не оценивались.
Список QMediaFormat неполон относительно фактически работающих образцов:
AV1, VP9 и Opus прошли тесты, хотя не вошли в возвращённый список этого API.

## Возможные следующие изменения

Только после отдельного согласования: расширить входной фильтр и ассоциации
для реально проверенных форматов; учитывать наличие видеопотока у OGG;
отдельно исследовать seek в TS с редкими ключевыми кадрами. В этом аудите
исправлений приложения и нового FIX нет.

## Полная матрица

| Образец | Видео / профиль | Аудио | Результат | Примечание |
|---|---|---|---|---|
| mp4-avc-baseline.mp4 | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mp4-avc-high.mp4 | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK | Фактический профиль Constrained Baseline; настоящий High проверен отдельным high-cabac образцом. |
| mp4-avc-10bit.mp4 | h264 / High 10 / yuv420p10le | aac / LC / 48000 / 2 | OK |  |
| mp4-avc-444.mp4 | h264 / High 4:4:4 Predictive / yuv444p | aac / LC / 48000 / 2 | OK |  |
| mp4-hevc-8bit.mp4 | hevc / Main / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mp4-hevc-10bit.mp4 | hevc / Main 10 / yuv420p10le | aac / LC / 48000 / 2 | OK |  |
| mp4-av1.mp4 | av1 / Main / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mkv-hevc-8bit.mkv | hevc / Main / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mkv-hevc-10bit.mkv | hevc / Main 10 / yuv420p10le | aac / LC / 48000 / 2 | OK |  |
| mkv-av1.mkv | av1 / Main / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mp4-mpeg4.mp4 | mpeg4 / Simple Profile / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mkv-avc.mkv | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mkv-vp9.mkv | vp9 / Profile 0 / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mkv-ffv1.mkv | ffv1 / yuv420p | flac / 48000 / 2 | OK |  |
| mkv-avc-ac3.mkv | h264 / Constrained Baseline / yuv420p | ac3 / 48000 / 2 | OK |  |
| mkv-avc-eac3.mkv | h264 / Constrained Baseline / yuv420p | eac3 / 48000 / 2 | OK |  |
| mkv-avc-dca.mkv | h264 / Constrained Baseline / yuv420p | dts / DTS / 48000 / 2 | OK |  |
| mkv-avc-truehd.mkv | h264 / Constrained Baseline / yuv420p | truehd / 48000 / 2 | OK |  |
| mkv-avc-flac.mkv | h264 / Constrained Baseline / yuv420p | flac / 48000 / 2 | OK |  |
| avi-mpeg4.avi | mpeg4 / Simple Profile / yuv420p | mp3 / 48000 / 2 | OK |  |
| avi-xvid.avi | mpeg4 / Simple Profile / yuv420p | mp3 / 48000 / 2 | OK |  |
| avi-msmpeg4v3.avi | msmpeg4v3 / yuv420p | mp3 / 48000 / 2 | OK |  |
| avi-mjpeg.avi | mjpeg / Baseline / yuvj420p | mp3 / 48000 / 2 | OK |  |
| avi-huffyuv.avi | huffyuv / yuv422p | mp3 / 48000 / 2 | OK |  |
| mov-avc.mov | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mov-prores.mov | prores / Standard / yuv422p10le | pcm_s16le / 48000 / 2 | OK |  |
| mov-dnxhr.mov | dnxhd / DNXHR LB / yuv422p | pcm_s16le / 48000 / 2 | OK |  |
| mov-animation.mov | qtrle / rgb24 | pcm_s16le / 48000 / 2 | OK |  |
| webm-vp8.webm | vp8 / 0 / yuv420p | vorbis / 48000 / 2 | OK |  |
| webm-vp9.webm | vp9 / Profile 0 / yuv420p | opus / 48000 / 2 | OK |  |
| webm-vp9-10bit.webm | vp9 / Profile 2 / yuv420p10le | opus / 48000 / 2 | OK |  |
| webm-av1.webm | av1 / Main / yuv420p | opus / 48000 / 2 | OK |  |
| m4v-avc.m4v | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK |  |
| wmv-wmv1.wmv | wmv1 / yuv420p | wmav2 / 48000 / 2 | OK |  |
| wmv-wmv2.wmv | wmv2 / yuv420p | wmav2 / 48000 / 2 | OK |  |
| mpeg-mpeg1.mpeg | mpeg1video / yuv420p | mp2 / 48000 / 2 | OK |  |
| mpeg-mpeg2.mpeg | mpeg2video / Main / yuv420p | mp2 / 48000 / 2 | OK |  |
| mpg-mpeg2.mpg | mpeg2video / Main / yuv420p | mp2 / 48000 / 2 | OK |  |
| ts-avc.ts | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK; ограничение перемотки | Без перемотки до конца: OK; после seek нет новых видеокадров. Повторено напрямую в Qt. |
| ts-hevc.ts | hevc / Main / yuv420p | ac3 / 48000 / 2 | OK |  |
| ts-mpeg2.ts | mpeg2video / Main / yuv420p | mp2 / 48000 / 2 | OK |  |
| m2ts-avc.m2ts | h264 / Constrained Baseline / yuv420p | ac3 / 48000 / 2 | OK; ограничение перемотки | Без перемотки до конца: OK; после seek нет новых видеокадров. Повторено напрямую в Qt. |
| mp3-cbr.mp3 | — | mp3 / 48000 / 2 | OK |  |
| mp3-vbr.mp3 | — | mp3 / 48000 / 2 | OK |  |
| flac-16bit.flac | — | flac / 48000 / 2 | OK |  |
| flac-24bit.flac | — | flac / 48000 / 2 | OK |  |
| wav-16bit.wav | — | pcm_s16le / 48000 / 2 | OK |  |
| wav-24bit.wav | — | pcm_s24le / 48000 / 2 | OK |  |
| wav-float32.wav | — | pcm_f32le / 48000 / 2 | OK |  |
| wav-51.wav | — | pcm_s16le / 48000 / 6 | OK |  |
| ogg-vorbis.ogg | — | vorbis / 48000 / 2 | OK |  |
| ogg-flac.ogg | — | flac / 48000 / 2 | OK |  |
| opus.opus | — | opus / 48000 / 2 | OK |  |
| m4a-aac.m4a | — | aac / LC / 48000 / 2 | OK |  |
| m4a-alac.m4a | — | alac / 48000 / 2 | OK |  |
| aac-adts.aac | — | aac / LC / 48000 / 2 | OK |  |
| outside-wma.wma | — | wmav2 / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| outside-ac3.ac3 | — | ac3 / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| outside-aiff.aiff | — | pcm_s16be / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| outside-wavpack.wv | — | wavpack / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| outside-ogv.ogv | theora / yuv420p | vorbis / 48000 / 2 | Не принимается расширение | Расширение не принимается. Прямое декодирование Qt OK; EndOfMedia не получен при position=duration. |
| outside-flv.flv | flv1 / yuv420p | mp3 / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| outside-3gp.3gp | mpeg4 / Simple Profile / yuv420p | aac / LC / 48000 / 2 | Не принимается расширение | Расширение не принимается Aureon; прямое воспроизведение Qt прошло. |
| mp4-avc-high-cabac.mp4 | h264 / High / yuv420p | aac / LC / 48000 / 2 | OK |  |
| mp4-av1-10bit.mp4 | av1 / Main / yuv420p10le | aac / LC / 48000 / 2 | OK |  |
| mkv-hevc-444.mkv | hevc / Rext / yuv444p | aac / LC / 48000 / 2 | OK |  |
| mp4-hevc-hdr10-metadata.mp4 | hevc / Main 10 / yuv420p10le | aac / LC / 48000 / 2 | OK | Main 10 с BT.2020/PQ метаданными; точность HDR/тонмаппинга не проверялась. |
| m2ts-bdav-avc.m2ts | h264 / High / yuv420p | ac3 / 48000 / 2 | OK; ограничение перемотки | Без перемотки до конца: OK; после seek нет новых видеокадров. Повторено напрямую в Qt. OpenCV также не выдал кадр после seek. |
| flac-96khz.flac | — | flac / 96000 / 2 | OK |  |
| flac-192khz.flac | — | flac / 192000 / 2 | OK |  |
| mp3-44100-mono.mp3 | — | mp3 / 44100 / 1 | OK |  |
| ts-avc-short-gop.ts | h264 / High / yuv420p | aac / LC / 48000 / 2 | OK |  |
| m2ts-avc-short-gop.m2ts | h264 / High / yuv420p | ac3 / 48000 / 2 | OK |  |
| ts-avc-long-gop.ts | h264 / Constrained Baseline / yuv420p | aac / LC / 48000 / 2 | OK; ограничение перемотки | Без перемотки до конца: OK; после seek нет новых видеокадров. Повторено напрямую в Qt. |
| ogg-theora-video.ogg | theora / yuv420p | vorbis / 48000 / 2 | Видео скрыто классификацией | Декодирование OK, но Aureon считает .ogg аудио и скрывает видео. EndOfMedia не получен. |
| m4a-opus.m4a | — | opus / 48000 / 2 | OK |  |
| wav-mp3.wav | — | mp3 / 48000 / 2 | OK |  |
| wav-adpcm.wav | — | adpcm_ima_wav / 48000 / 2 | OK |  |
| mp4-vp9-opus.mp4 | vp9 / Profile 0 / yuv420p | opus / 48000 / 2 | OK |  |

[К обзору форматов](media-formats.ru.md) · [English summary](media-formats.md) · [К README](../README.ru.md)
