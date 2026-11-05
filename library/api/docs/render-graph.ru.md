# Проходы, аудиотекстура и постобработка

[← API](../README.ru.md) · [English](render-graph.md)

`scene.multipass.experimental.v1`: `multipass.passes` и `multipass.inputs`.
Проход задаёт id, shader, size, inputs; необязательны format/filter/wrap/uniforms/libraries/quality.
Размер задаётся либо fixed [width,height], либо scale 0.125–1.0. Форматы rgba8/rgba16f,
фильтр linear/nearest, wrap clamp/repeat. У каждого прохода файл `shaders/mp_<id>.frag`.
Доступны `u_mp_delta` и `u_mp_frame`.

Input edge ссылается на texture, audio spectrum либо pass + frame current/previous.
current читает только ранее выполненный проход; previous — предыдущую завершённую историю.
Feedback использует ping-pong; одновременное чтение текущей цели записи не разрешено.
Повтор кадра с теми же часами не должен продвигать историю. Скачок/возврат времени
и изменение размера могут сбрасывать её. Это не готовые TAA/reprojection/motion vectors.

`scene.audio_texture.experimental.v1`: поле `audio_texture.sampler`, read-only RG32F 32×1.
R содержит опубликованные bands, G — peaks. Значения и порядок совпадают с массивами uniforms;
дополнительного анализа и скрытого gain нет. В графе ресурс читается через audio="spectrum".

Hybrid background читает результаты общего графа через `hybrid.background.inputs` при
`scene.hybrid_background_inputs.experimental.v1`. Фон использует общую камеру и часы;
отдельный behavior.camera в нём запрещён. Глубина должна соответствовать геометрии фона.

Порядок: общий Multipass → тени/отражения → фон → геометрия → штатный fog →
snapshot colour/depth → авторский post_geometry → AA/масштабирование → интерфейс.
`scene.post_geometry.experimental.v1` работает в основной камере; входы read-only,
запись `gl_FragDepth` запрещена. Depth описывает непрозрачные поверхности/фон,
не отдельные слои прозрачности и объёма. Отражение авторского post-volume автоматически не строится.

До 8 проходов, 8 inputs на программу, ось до 8192 и 512 МиБ суммарных пар history buffers.
Это отдельные профильные ограничения, а не все общие лимиты контейнера ×100.
