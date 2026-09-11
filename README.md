# 🎫 Ticket Bot — Telegram бот для поиска дешёвых билетов

Бот ищет и сравнивает дешёвые **авиабилеты** (Aviasales) и **билеты на поезд** (РЖД) по России. Поддерживает мониторинг цен и уведомления при снижении стоимости.

## Возможности

- ✈️ Поиск авиабилетов через Aviasales (Победа, S7, Аэрофлот, Utair и др.)
- 🚂 Поиск билетов на поезд через pass.rzd.ru
- 📍 Сравнение цен из **нескольких городов** одновременно (например, Иваново vs Москва vs Ярославль)
- 📅 Поиск в диапазоне дат (±1–3 дня от целевой даты)
- 🔔 Периодический мониторинг — уведомление при достижении нужной цены
- 🛒 Прямые ссылки на покупку билетов

## Команды

| Команда | Описание |
|---------|----------|
| `/search <откуда> <куда> <дата> [дней]` | Разовый поиск |
| `/watch <откуда> <куда> <дата> <порог₽>` | Запустить мониторинг |
| `/list` | Список активных мониторингов |
| `/stop <id>` | Остановить мониторинг |
| `/cities` | Список поддерживаемых городов |
| `/sources` | Статус источников данных |
| `/help` | Справка |

**Примеры:**
```
/search Москва Казань 2026-08-10 2
/search Иваново,Москва,Ярославль Казань 2026-08-10 2
/watch Иваново,Москва Казань 2026-08-10 3500
```

## Установка

### 1. Клонировать репозиторий
```bash
git clone https://github.com/Egorhio/ticket-bot.git
cd ticket-bot
```

### 2. Установить зависимости
```bash
pip install -r requirements.txt
```

### 3. Настроить токены
```bash
cp .env.example .env
```
Откройте `.env` и заполните:

| Переменная | Где получить |
|-----------|-------------|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) в Telegram → `/newbot` |
| `AVIASALES_TOKEN` | [travelpayouts.com](https://www.travelpayouts.com) → Инструменты → API |
| `CHECK_INTERVAL_HOURS` | Интервал проверки мониторингов (часы, по умолчанию 1) |

### 4. Запустить
```bash
python bot.py
```

## Стек технологий

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) ≥ 21.0
- [APScheduler](https://apscheduler.readthedocs.io/) — планировщик мониторингов
- [aiosqlite](https://github.com/omnilib/aiosqlite) — асинхронная SQLite БД
- [Travelpayouts Data API](https://support.travelpayouts.com/hc/en-us/articles/203956163) — кэш цен Aviasales
- РЖД pass.rzd.ru — неофициальный API поездов

## Лицензия

MIT — см. файл [LICENSE](LICENSE)
