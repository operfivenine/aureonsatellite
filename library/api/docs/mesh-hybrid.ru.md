# Mesh / Hybrid

[← API](../README.ru.md) · [English](mesh-hybrid.md)

Базовый Mesh и Hybrid используют разные профили. Hybrid требует
`scene.mesh.experimental.v1`, `scene.hybrid_mesh.experimental.v1`, `scene.standard_library.v1`.
Геометрия, camera, environment, quality и диапазоны батчей валидируются до создания GL-ресурсов.
Для дополнительных полей нужны отдельные features материалов, bindings, анимации и object graph.

Поддержаны текстуры материалов, UV/tangent, albedo/normal/ORM, sampler bindings,
прозрачность, отражения, выбор источников света и штатный ограниченный volumetric fog.
UV/tangent меняет раскладку mesh-вершин только при явном объявлении соответствующего feature.
Старые mesh-ресурсы сохраняют прежнюю раскладку. Имена sampler используют `u_tex_`.
Нельзя подменять одну текстуру другим типом ресурса или занимать уже используемое имя.

GPU procedural instances используют `gl_InstanceID` и объявленное число экземпляров.
Залпы opt-in ограничены историей 2–16 slots и 3–256 lanes; число instances должно
равняться slots × lanes. Lifetime 1–60 с; минимальный интервал не меньше 0.25 с.
Должно хватать slots для всех живых залпов. Массив `u_mesh_volleys` объявляется в vertex
с точным числом slots. Самостоятельные texture samplers в текущем vertex-профиле запрещены.

Дополнения patterns/signals задают интервал и выбор паттерна выражениями;
signal-driven emitter требует mesh bindings. `travel_clock` разрешён с
`scene.mesh_volley_clock.experimental.v1` и `scene.mesh_volley_signals.experimental.v1`:
возраст перемещения считается относительно интегрируемых авторских часов.
Это отдельная возможность от `camera.clock` и не изменение DSP.


Ресурсные бюджеты: [реестр возможностей](../reference/FEATURE_REGISTRY.json).
