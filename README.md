# Модуль параметрического 3D-моделирования (ВКР)


- ядро параметров с зависимостями и пересчётом;
- признаки построения (`box`, `cylinder`, `extrude`);
- сценарный язык;
- веб-интерфейс с 3D-просмотром;
- экспорт **STL** и инженерные расчёты (объём, центр масс, масса).

Полный текст дипломной работы: [docs/DIPLOMNAYA_RABOTA.md](docs/DIPLOMNAYA_RABOTA.md).

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Вариант 1: веб-приложение (рекомендуется)

```bash
python web_app.py
```

Далее открой `http://127.0.0.1:8000` в браузере.

В интерфейсе доступны:

- загрузка шаблонов из `examples/*.txt`;
- быстрый конструктор команд (`param`, `box`, `cylinder`, `extrude`);
- редактирование сценария в окне;
- запуск пересборки модели;
- интерактивный 3D-просмотр;
- таблица параметров и инженерных характеристик;
- скачивание STL-файла;
- сохранение/загрузка проекта (текст сценария);
- экспорт инженерного отчёта в CSV.

Горячая клавиша построения: `Cmd+Enter` (или `Ctrl+Enter`).

### Вариант 2: CLI

```bash
python main.py examples/simple_box.txt -o model.stl
python main.py examples/bracket.txt -o bracket.stl
python main.py examples/cylinder_mount.txt -o cylinder.stl
```

Опция `--density` в CLI задаёт плотность (кг/м³) для расчёта массы; по умолчанию 7850.

## Команды сценария

| Команда | Описание |
|--------|----------|
| `param ИМЯ ЧИСЛО` | константный параметр |
| `param ИМЯ ЧИСЛО expr ФОРМУЛА` | параметр, вычисляемый из других |
| `box ID cx cy cz dx dy dz` | параллелепипед; все поля — **имена** параметров |
| `cylinder ID cx cy cz R H [x\|y\|z \| axis x\|y\|z]` | цилиндр; последний токен — ось (по умолчанию z) |
| `extrude ID высота x1 y1 x2 y2 …` | замкнутый контур в XY, экструзия вдоль Z |

Строки с `#` — комментарии.

## Структура кода

- `parametric_cad/parameters.py` — граф зависимостей и пересчёт
- `parametric_cad/features.py` — геометрия признаков
- `parametric_cad/scripting.py` — разбор сценария
- `main.py` — CLI
- `web_app.py` — backend веб-приложения (Flask)
- `web/templates/index.html` — интерфейс пользователя
- `web/static/app.js` — логика UI и 3D-визуализация (локальный Canvas-renderer)
- `web/static/styles.css` — стили интерфейса
- `docs/DEFENSE_CHECKLIST.md` — чек-лист готовности к защите
- `docs/DEFENSE_DEMO_SCRIPT.md` — сценарий демонстрации на защите
- `docs/PRESENTATION_PLAN.md` — структура слайдов презентации

## Ограничения прототипа

Нет булевых операций между телами и формата STEP; выражения — только арифметика с параметрами.

## Материалы для защиты

- `docs/DIPLOMNAYA_RABOTA.md` — текст пояснительной записки ВКР
- `docs/PRESENTATION_PLAN.md` — план структуры презентации
- `docs/DEFENSE_DEMO_SCRIPT.md` — пошаговый сценарий live-демонстрации
- `docs/DEFENSE_CHECKLIST.md` — финальный чек-лист готовности к защите
