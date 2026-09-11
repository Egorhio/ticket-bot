"""
Главный файл Telegram-бота для поиска дешёвых авиа и ж/д билетов.
Поддерживает несколько городов отправления через запятую.
Запуск: python bot.py
"""

import logging
from datetime import date

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TimedOut, NetworkError

from config import BOT_TOKEN, AVIASALES_TOKEN
from cities import find_city, parse_origins, city_display_name, list_cities
from flights import get_cheap_flights, format_flights, compare_flights
from trains import get_cheap_trains, format_trains, compare_trains
from database import init_db, add_monitor, get_user_monitors, deactivate_monitor
from scheduler import setup_scheduler

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = """
🎫 *Бот поиска дешёвых билетов* (авиа + РЖД)

*Источники данных:*
• Aviasales — агрегатор (Победа, S7, Аэрофлот, Utair…), кэш 48ч
• РЖД pass.rzd.ru — поезда

*Команды:*

/search <откуда> <куда> <дата> [дней]
  Один или несколько городов — через запятую
  Пример: `/search Москва Казань 2026-08-10 2`
  Мульти: `/search Иваново,Москва,Ярославль Казань 2026-08-10 2`

/watch <откуда> <куда> <дата> <порог₽>
  Мониторинг — уведомит при снижении цены
  Пример: `/watch Иваново,Москва Казань 2026-08-10 3500`

/sources — статус подключённых источников
/list — ваши активные мониторинги
/stop <id> — остановить мониторинг
/cities — список городов
/help — эта справка
"""


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Привет! Я ищу и сравниваю дешёвые авиабилеты и поезда.\n" + HELP_TEXT,
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def cmd_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    av = "✅ подключён" if AVIASALES_TOKEN else "❌ нет токена (добавьте AVIASALES\\_TOKEN в .env)"
    await update.message.reply_text(
        "*Источники данных:*\n\n"
        f"✈️ *Aviasales* (агрегатор, кэш 48ч): {av}\n"
        f"   Покрывает: Победа, S7, Аэрофлот, Utair, Уральские, Nordwind…\n\n"
        f"🚂 *РЖД pass.rzd.ru* (поезда): ✅ всегда активен",
        parse_mode="Markdown",
    )


async def cmd_cities(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"🌆 *Поддерживаемые города* (✈️🚂 = авиа+поезд, 🚂 = только поезд):\n\n{list_cities()}",
        parse_mode="Markdown",
    )


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if len(args) < 3:
        await update.message.reply_text(
            "❌ Использование:\n"
            "`/search <откуда> <куда> <дата> [дней]`\n\n"
            "Один город: `/search Москва Казань 2026-08-10 2`\n"
            "Несколько: `/search Иваново,Москва,Ярославль Казань 2026-08-10 2`",
            parse_mode="Markdown",
        )
        return

    origin_names = parse_origins(args[0])
    dest_name = args[1]
    date_str = args[2]
    days_range = min(int(args[3]), 3) if len(args) > 3 else 2

    # Валидация городов
    dest_info = find_city(dest_name)
    if not dest_info:
        await update.message.reply_text(
            f"❌ Город назначения «{dest_name}» не найден. /cities"
        )
        return

    valid_origins = []
    invalid = []
    for name in origin_names:
        info = find_city(name)
        if info:
            valid_origins.append((name, info))
        else:
            invalid.append(name)

    if invalid:
        await update.message.reply_text(
            f"❌ Не найдены города: {', '.join(invalid)}\nПроверьте /cities"
        )
        return
    if not valid_origins:
        return

    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        await update.message.reply_text("❌ Формат даты: ГГГГ-ММ-ДД, например 2026-08-10")
        return

    origins_label = ", ".join(n.title() for n, _ in valid_origins)
    msg = await update.message.reply_text(
        f"🔍 Ищу: {origins_label} → {dest_name.title()}\n"
        f"Дата: {date_str} (±{days_range} дн.)..."
    )

    multi = len(valid_origins) > 1

    if multi:
        flight_origins = [
            (name, info["iata"])
            for name, info in valid_origins
            if not info.get("no_flights") and info.get("iata")
        ]
        train_origins = [(name, info["rzd_code"]) for name, info in valid_origins]

        flight_text = compare_flights(flight_origins, dest_info["iata"], target_date, days_range)
        train_text = compare_trains(train_origins, dest_info["rzd_code"], target_date, days_range)
        result = f"{flight_text}\n\n{train_text}"
    else:
        name, info = valid_origins[0]
        has_flights = not info.get("no_flights") and info.get("iata")

        if has_flights:
            if AVIASALES_TOKEN:
                flights = get_cheap_flights(info["iata"], dest_info["iata"], target_date, days_range)
                flight_text = format_flights(flights)
            else:
                flight_text = "✈️ Aviasales: токен не задан (AVIASALES\\_TOKEN в .env)"
        else:
            flight_text = f"✈️ {name.title()} — нет регулярных авиарейсов"

        trains = get_cheap_trains(info["rzd_code"], dest_info["rzd_code"], target_date, days_range)
        train_text = format_trains(trains)
        result = f"{flight_text}\n\n{train_text}"

    await msg.edit_text(result, parse_mode="Markdown")


async def cmd_watch(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    args = ctx.args
    if len(args) < 4:
        await update.message.reply_text(
            "❌ Использование:\n"
            "`/watch <откуда> <куда> <дата> <порог₽>`\n\n"
            "Пример: `/watch Иваново,Москва Казань 2026-08-10 3500`",
            parse_mode="Markdown",
        )
        return

    origin_names = parse_origins(args[0])
    dest_name = args[1]
    date_str = args[2]

    try:
        threshold = int(args[3])
        date.fromisoformat(date_str)
    except ValueError:
        await update.message.reply_text("❌ Проверьте формат: дата ГГГГ-ММ-ДД, порог — целое число ₽")
        return

    dest_info = find_city(dest_name)
    if not dest_info:
        await update.message.reply_text(f"❌ Город «{dest_name}» не найден. /cities")
        return

    invalid = [n for n in origin_names if not find_city(n)]
    if invalid:
        await update.message.reply_text(
            f"❌ Не найдены города: {', '.join(invalid)}\nПроверьте /cities"
        )
        return

    monitor_id = await add_monitor(
        chat_id=update.effective_chat.id,
        origins=[n.lower() for n in origin_names],
        destination=dest_name.lower(),
        travel_date=date_str,
        days_range=2,
        threshold=threshold,
    )

    origins_label = ", ".join(n.title() for n in origin_names)
    await update.message.reply_text(
        f"✅ Мониторинг *#{monitor_id}* создан!\n"
        f"Маршрут: {origins_label} → {dest_name.title()}\n"
        f"Дата: {date_str} (±2 дн.)  |  Порог: *{threshold:,} ₽*\n\n"
        f"Проверка каждые {ctx.application.bot_data.get('interval_hours', 6)} ч.\n"
        f"Остановить: /stop {monitor_id}",
        parse_mode="Markdown",
    )


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    monitors = await get_user_monitors(update.effective_chat.id)
    if not monitors:
        await update.message.reply_text("У вас нет активных мониторингов. Создайте через /watch")
        return

    lines = ["📋 *Ваши активные мониторинги:*\n"]
    for m in monitors:
        origins = m["origins"]
        origins_str = ", ".join(o.title() for o in origins)
        lines.append(
            f"*#{m['id']}* {origins_str} → {m['destination'].title()}\n"
            f"   Дата: {m['travel_date']}  Порог: {m['threshold']:,} ₽\n"
            f"   Создан: {m['created_at'][:10]}"
        )
    await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")


async def cmd_stop(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not ctx.args:
        await update.message.reply_text("❌ Укажите ID: /stop <id>")
        return
    try:
        monitor_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID должен быть числом.")
        return

    ok = await deactivate_monitor(monitor_id, update.effective_chat.id)
    if ok:
        await update.message.reply_text(f"✅ Мониторинг #{monitor_id} остановлен.")
    else:
        await update.message.reply_text(f"❌ Мониторинг #{monitor_id} не найден или уже остановлен.")


async def error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(ctx.error, (TimedOut, NetworkError)):
        logger.warning(f"Сетевая ошибка (игнорируем): {ctx.error}")
    else:
        logger.error(f"Необработанная ошибка: {ctx.error}", exc_info=ctx.error)


async def post_init(app: Application) -> None:
    """Вызывается после старта бота — инициализируем БД и планировщик."""
    await init_db()
    scheduler = setup_scheduler(app.bot)
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    logger.info("БД и планировщик инициализированы.")


async def post_shutdown(app: Application) -> None:
    scheduler = app.bot_data.get("scheduler")
    if scheduler:
        scheduler.shutdown(wait=False)


def main() -> None:
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.bot_data["interval_hours"] = 6

    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("sources", cmd_sources))
    app.add_handler(CommandHandler("cities", cmd_cities))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("watch", cmd_watch))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("stop", cmd_stop))

    logger.info("Бот запущен. Ctrl+C для остановки.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
