# Отличия от поставки для Aureon 0.22.3 · v367

[← API](../README.ru.md) · [English](changes.md)

`aurs.standard` остаётся 1.1; базовый format_version и engine.api_major остаются 1.
Справочник собран по текущим схемам, без тематических примеров.

- Расширены mesh assets, UV/tangent, texture/material bindings и бюджеты ресурсов.
- Поддержаны GPU procedural instances, музыкальные залпы, их patterns/signals и объёмный свет.
- Добавлены buffer graph с feedback, опубликованная спектральная текстура, входы Hybrid background
  и read-only post_geometry colour/depth.
- Добавлены палитра трека и native-текст заголовка через текстурный атлас.
- Hybrid получил opt-in history signals и независимые часы перемещения залпов.
- Добавлены общие scene-clock камеры Hybrid и прямые cuts камер fullscreen v2.
- Сохранены региональные атаки, Reactive controls, Advanced и поведение пакетов без новых opt-in.

Это возможности хоста. Новые темы и способы построения их сцен не поставляются в этой библиотеке.

## Ноябрьская редакция API 1.1

5 ноября 2026 поддержанные экспериментальные возможности получили стабильный статус.
Технические имена, данные и код не менялись. [Точная политика совместимости](stability.ru.md).
