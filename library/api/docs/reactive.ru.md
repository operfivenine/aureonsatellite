# Аудио и декларативное поведение

[← API](../README.ru.md) · [English](reactive.md)

Входы `audio.low/mid/high`, энергия и региональные атаки имеют разный смысл.
`audio.low_attack/mid_attack/high_attack` требуют `audio.regional_attacks.v2`.
В режиме v1 региональные атаки нейтральны: автор определяет допустимое поведение через
прежние уровни, если эффект должен работать в обоих движках. Нового FFT или отдельного BPM API нет.

Fullscreen v2 публикует `u_bands[32]`, `u_peaks[32]`, `u_events[8]` и типизированные
reserved uniforms. Исходные 64 полосы анализатора не равны 32 опубликованным значениям.
Панельный спектр — отдельный opt-in `scene.spectrum_panels.v1` и 16 столбцов
с renderer-rate сглаживанием, включаемый через `behavior.spectrum_panels`.

`behavior.reactive_controls` явно объявляет поддержанные органы управления;
required feature — `behavior.reactive_controls.v1`. Выражения `runtime.bump`,
`bump_strength`, `low_gain`, `mid_gain`, `high_gain`, `light_pulse`, `release_scale`
требуют согласованных объявлений. Bump, диапазоны и Light Pulse должны независимо
влиять на свой эффект; повторное умножение одного gain непреднамеренно меняет масштаб.

Сигналы v2: expression, integrator, envelope, derivative, spring, state, history,
а также разрешённые именованные presets. Граф ограничен и упорядочивается по зависимостям.
История допускает mean/max/min/interval/rate; окно 0.1–10 с; interval/rate используют
порог, минимальный интервал, stale и 2–32 события. Это bounded история сигналов,
не произвольная память пакета и не оценка BPM, гарантированная для любого трека.

Для `history` в Hybrid требуется `scene.mesh_history_signals.experimental.v1`;
каналы Hybrid ограничены отдельно и не равны всей таблице fullscreen v2.
Типичные непрерывные движения используют интегратор и delta-time; пауза, seek и смена
движка обрабатываются хостом, а автор не должен повторно воспроизводить прошлые атаки.


Точные каналы и типы: [машинный справочник](../reference/UNIFORMS_AND_CHANNELS.json).

В индексе u_events[8] обозначает исходный размер event-массива. Профиль допускает явный размер в пределах лимита event_slots; массив должен вмещать все объявленные слоты событий. Не считайте 8 универсальным пределом всех расширений.
