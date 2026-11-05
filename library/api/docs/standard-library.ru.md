# Стандартная библиотека GLSL

[← API](../README.ru.md) · [English](standard-library.md)

Для нового fullscreen v2 указывается `libraries: ["aurs.standard"]` и соответствующий
required feature `scene.standard_library.v1`. Hybrid требует стандартную библиотеку
и в manifest, и в общем background. Разрешён GLSL `#version 330 core`;
авторские `#include`/произвольные директивы не поддерживаются. Определения качества задаются JSON.

Пространство функций `aur_` принадлежит хосту: нельзя переопределять его в своём шейдере.
Восемь разделов стандартной библиотеки: Camera, Reactive, Environment, Objects,
Lighting, Atmosphere, Motion, Presentation. Это разделы API, а не восемь GPU-проходов.

Функции с аргументами, структуры и зависимости перечислены в [машинном справочнике](../reference/STANDARD_LIBRARY_SYMBOLS.json). В публичном издании к сигнатурам добавлены проверенные возвращаемые типы и поля структур. См. [читаемый индекс](glsl-symbols.ru.md).

Библиотеку подставляет Aureon при загрузке пакета. Копировать её реализацию в тему не требуется. Необязательные модули не включаются автоматически: проверяйте public_libraries, legacy_libraries и requires. Внутренняя ревизия реализации не используется как версия пакета автора.
