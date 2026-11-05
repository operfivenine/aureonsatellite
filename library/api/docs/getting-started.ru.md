# Как подготовить первый AURS-пакет

[← API](../README.ru.md) · [English](getting-started.md)

1. Сначала выберите renderer: fullscreen v2 — для сцены на основе шейдера; Mesh — для базовой геометрии; Hybrid — для геометрии с общим процедурным фоном. См. [таблицу профилей](contract.ru.md).
2. Задайте собственный dotted ID и версию из трёх чисел. При обновлении той же сцены обычно сохраняют ID и повышают версию; не занимайте чужой ID для другой сцены.
3. Объявите только используемые required features/capabilities выбранного профиля. Копируйте точные ID из [реестра](../reference/FEATURE_REGISTRY.json), включая историческое слово `experimental`.
4. Подготовьте `scene.json` для этого renderer, затем объявленные шейдеры и ресурсы. Сначала добейтесь читаемой композиции и камеры, затем добавляйте дорогие эффекты и музыкальную реакцию.
5. Упакуйте содержимое в ZIP с `manifest.json` и `scene.json` в корне и расширением `.aurs`. Переименование произвольного ZIP само по себе не создаёт рабочую сцену.
6. В отдельном тестовом профиле импортируйте пакет через **Settings → Visuals → Import scene**, затем выберите его в Scene Picker. При ошибке используйте точный текст сообщения. Успешный импорт ещё требует проверки GLSL и GPU в программе.
7. Пройдите [проверку перед выпуском](release-checklist.ru.md), запишите версию Aureon, ОС/GPU и настройки теста. Пакет `.aurs` распространяется отдельно от установщика плеера.

## Пример manifest

Это только пример контракта manifest, не готовая сцена. Для рабочего пакета ещё нужны `scene.json`, шейдеры, ресурсы и согласованные зависимости. Добавляйте required features для реально используемых расширений.

```json
{
  "format": "aureon.theme",
  "package_type": "scene",
  "format_version": 1,
  "id": "org.example.my_scene",
  "version": "1.0.0",
  "name": {
    "en": "My Scene",
    "ru": "Моя сцена"
  },
  "author": {
    "name": "Your name"
  },
  "engine": {
    "api_major": 1,
    "min_aureon": "0.23.0"
  },
  "renderer": "scene.fullscreen_frag.v2",
  "entry": "scene.json",
  "features": {
    "required": [
      "scene.fullscreen_frag.v2",
      "scene.quality.v1",
      "scene.uniforms.v1",
      "scene.shaderlib.v1",
      "scene.standard_library.v1"
    ],
    "optional": []
  },
  "capabilities": {
    "required": [
      "audio.reactive.v1",
      "time.elapsed.v1"
    ],
    "optional": []
  },
  "parameters": {}
}
```

Не добавляйте произвольные поля BPM, пути трека, Python callbacks или окна интерфейса. Хост предоставляет только документированные входы. См. [структуру пакета](package.ru.md), [аудио](reactive.ru.md) и [рекомендации автору](authoring-recommendations.ru.md).
