# Поля сцены: основные профили

[← API](../README.ru.md) · [English](scene-fields.md)

Это справочник основных точек входа, не полная JSON Schema. Вложенные необязательные объекты имеют собственные обязательные поля и feature-зависимости.

## Fullscreen v1/v2

| Поле | Назначение |
| --- | --- |
| `shader` | Обязательно; строго `shaders/main.frag` |
| `quality` | Объекты пресетов с defines; v1 — low/medium/high, v2 также допускает объявленный extreme |
| `signals` | Именованные ограниченные дескрипторы сигналов |
| `uniforms` | Привязки авторских uniforms к выражениям и векторам выражений |
| Дополнения v2 | behavior, libraries, textures, lights, graphics, multipass, audio_texture |

Все пресеты объявляют одинаковые имена quality defines. Это идентификаторы в верхнем регистре, без префикса GL_ и двойного подчёркивания; значения — целые числа. Обычные пределы положительны, boolean graphics bindings используют 0/1. Не добавляйте собственные #define в шейдер.

Авторский uniform связывает от одного до четырёх компонентов выражения: float/vec2/vec3/vec4. Допустим объект с type и source, если тип соответствует числу компонентов. В GLSL нужно объявить то же имя и тип. Нельзя занимать reserved-имена хоста, префиксы u_audio_/u_lightcfg_, имена массивов и уже используемые samplers.

Fragment shader начинается с `#version 330 core` и содержит `void main()`. Допускается только эта version-директива; собственные includes/defines и неподдержанные операции отклоняются. Профиль AURS не является произвольным desktop GLSL.

### Фрагмент сглаженного отклика

Ниже фрагмент scene.json, не готовый пакет и не художественная сцена. В собственном шейдере нужны `uniform float u_low;`, применение отклика и собственное изображение. Define STEPS снижает нагрузку только тогда, когда шейдер действительно его использует.

К базовым fullscreen-v2 features из [примера manifest](getting-started.ru.md) добавьте для этого фрагмента `behavior.envelope.v1`, `behavior.temporal.v2`, `behavior.transport.v1` и `behavior.reactive_controls.v1`.

```json
{
  "shader": "shaders/main.frag",
  "libraries": [
    "aurs.standard"
  ],
  "quality": {
    "low": {
      "defines": {
        "STEPS": 24
      }
    },
    "medium": {
      "defines": {
        "STEPS": 48
      }
    },
    "high": {
      "defines": {
        "STEPS": 64
      }
    }
  },
  "signals": {
    "low": {
      "type": "envelope",
      "expr": "clamp(audio.low*runtime.low_gain*runtime.light_pulse*runtime.audio_active,0,1)",
      "attack": 0.06,
      "release": 0.4
    }
  },
  "uniforms": {
    "u_low": "signal.low"
  },
  "behavior": {
    "reactive_controls": [
      "low",
      "light_pulse",
      "release"
    ]
  }
}
```

## Mesh/Hybrid

Оба профиля требуют корневые объекты libraries, environment, quality, camera и statistics; Hybrid дополнительно требует hybrid. graphics и behavior необязательны при соблюдении зависимостей. Корневые расширения Hybrid: textures, materials, signals, object_graph, reflections, volley_emitter, volumetrics, vertex_layout, multipass, audio_texture, post_geometry, track_text.

| Объект | Основной контракт |
| --- | --- |
| libraries | Mesh: `["aurs.geometry.experimental"]`; Hybrid: `["aurs.geometry.experimental", "aurs.standard"]`, в таком порядке |
| environment | fog_color, fog_density, ambient, planet_fill, fill_origin |
| statistics | buildings, objects |
| camera | times, eyes, targets, fov, near, far, presets; необязательные micro_motion/clock требуют Hybrid-features |
| quality | low, medium, high обязательны; у каждого mesh и batches, defines необязателен |
| Mesh-ресурсы | meshes/low.bin, meshes/medium.bin, meshes/high.bin |
| Vertex layout | По умолчанию p3c4n3; p3c4n3uv2t4 требует UV/tangent-feature |
| hybrid.background | Обязательны shader, libraries, quality и uniforms; textures/inputs необязательны с зависимостями |

Число векторов камеры соответствует числу times; маршруты eyes/targets замыкаются. Presets, ресурсы и batches проходят дополнительные проверки. Mesh/Hybrid нужны соответствующие шейдеры и ресурс превью. Таблица не заменяет профильный валидатор и не разрешает переносить каждое расширение в любой объект.

См. [Mesh/Hybrid](mesh-hybrid.ru.md), [семантику камеры](cameras.ru.md) и [структуру пакета](package.ru.md).
