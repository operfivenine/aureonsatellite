# AURS API 1.1

**Ноябрь 2026 · stable · Aureon 0.23.0 / v385**

[English](README.md) · [Каталог AURS](https://github.com/operfivenine/aureonsatellite/blob/main/library/README.ru.md)

Публичный справочник для создания AURS-сцен. Редакция от 5 ноября 2026: контракт API 1.1 сохранён, поддержанные возможности имеют стабильный статус. Историческое слово `experimental` в технических ID нужно сохранять.

Начните с [первого пакета](docs/getting-started.ru.md) и [рекомендаций автору](docs/authoring-recommendations.ru.md). Затем выберите renderer и сверяйтесь с его возможностями, каналами и лимитами.

**[Скачать справочник ZIP](https://github.com/operfivenine/aureonsatellite/raw/refs/heads/main/library/Aureon-AURS-API-1.1-2026-11.zip)**

## Справочник

- [Начало работы](docs/getting-started.ru.md)
- [Рекомендации автору](docs/authoring-recommendations.ru.md)
- [Контракт и профили renderer](docs/contract.ru.md)
- [Структура и поля пакета](docs/package.ru.md)
- [Поля scene.json и фрагмент отклика](docs/scene-fields.ru.md)
- [Стандартная библиотека GLSL](docs/standard-library.ru.md)
- [Сигнатуры функций и структуры GLSL](docs/glsl-symbols.ru.md)
- [Аудио и Reactive](docs/reactive.ru.md)
- [Mesh / Hybrid](docs/mesh-hybrid.ru.md)
- [Проходы и постобработка](docs/render-graph.ru.md)
- [Камеры и время](docs/cameras.ru.md)
- [Палитра и текст трека](docs/track-inputs.ru.md)
- [Лимиты и графика](docs/limits-and-qa.ru.md)
- [Переносимость](docs/portability.ru.md)
- [Проверка перед выпуском](docs/release-checklist.ru.md)
- [Частые ошибки](docs/troubleshooting.ru.md)
- [Стабильность и прежние ID](docs/stability.ru.md)
- [Изменения ноябрьской редакции](docs/changes.ru.md)

## Машинные справочники

- [Feature registry](reference/FEATURE_REGISTRY.json)
- [Uniforms and audio channels](reference/UNIFORMS_AND_CHANNELS.json)
- [Standard-library symbol index](reference/STANDARD_LIBRARY_SYMBOLS.json)
- [Edition metadata](API_RELEASE.json)

## Состав и проверка

Комплект содержит документацию и индексы интерфейсов. Исходников плеера, реализации GLSL-библиотеки, исполняемых инструментов, готовых тем и их конструкций здесь нет. Стандартную библиотеку подставляет установленный Aureon; внешний Python для импорта AURS не нужен. В каждом разделе есть переключение EN/RU.

Приём контейнера, нативная компиляция GLSL, производительность и проверка каждой платформы — разные этапы. Поддержанные профили и правила stable-статуса описаны в [совместимости](docs/stability.ru.md).
