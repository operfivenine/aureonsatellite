# Контейнер и схемы

[← API](../README.ru.md) · [English](package.md)

AURS — ZIP с `manifest.json`, `scene.json` и ресурсами в разрешённых путях.
Для fullscreen обязателен `shaders/main.frag`; Mesh использует также `shaders/main.vert`
и бинарные ресурсы `meshes/`. Hybrid добавляет `shaders/background.frag`.
Авторские проходы имеют имена `shaders/mp_<id>.frag`; постобработка — `shaders/post_geometry.frag`.
Превью объявляется как `preview.png` и требует `scene.preview.v1`.

В manifest обязательны `format`, `package_type`, `format_version`, `id`, `version`, `name`,
`engine`, `renderer`, `entry`. `name` — словарь локализаций с обязательным `en`;
`version` имеет три числовые компоненты. ID — строчный dotted identifier, не путь.
`author` содержит только `name`. `parameters` в этом профиле допускает только пустой объект.
Неизвестные поля отклоняются, включая произвольные metadata-поля.

Запрещены ссылки, абсолютные пути, выход через `..`, дубликаты без учёта регистра,
исполняемые вложения и неиспользуемые ресурсы, для которых схема требует точное соответствие.
JSON читается как UTF-8; дубли полей и нечисловые NaN/Infinity отклоняются.

Fullscreen scene: `shader`, `quality`, `signals`, `uniforms`; v2 также `behavior`,
`libraries`, `textures`, `lights`, `graphics`, `multipass`, `audio_texture`.
Поля Mesh/Hybrid и их взаимные ограничения проверяются отдельно: нельзя переносить
поле одного renderer в другой лишь потому, что feature поддержан где-либо в хосте.


Точные названия полей зависят от renderer и контекста. Индекс внутренних проверок Python не является JSON Schema; объединять поля из разных объектов нельзя. Окончательную совместимость проверяет импорт в Aureon.
