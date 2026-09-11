"""
Периодическая проверка мониторингов и отправка уведомлений.
Поддерживает несколько городов отправления в одном мониторинге.
"""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from config import CHECK_INTERVAL_HOURS, AVIASALES_TOKEN
from database import get_active_monitors, mark_notified
from flights import get_cheap_flights
from trains import get_cheap_trains
from cities import find_city

logger = logging.getLogger(__name__)


async def check_monitors(bot: Bot) -> None:
    """Проверяет все активные мониторинги и шлёт уведомления при срабатывании."""
    monitors = await get_active_monitors()
    if not monitors:
        return

    logger.info(f"Проверяю {len(monitors)} мониторингов...")

    for m in monitors:
        try:
            target_date = date.fromisoformat(m["travel_date"])
            dest_info = find_city(m["destination"])
            if not dest_info:
                continue

            # Собираем результаты по каждому городу отправления
            hits: list[dict] = []  # {origin, type, price, detail}

            for origin_name in m["origins"]:
                origin_info = find_city(origin_name)
                if not origin_info:
                    continue

                # Авиабилеты — Aviasales (кэш)
                if AVIASALES_TOKEN and not origin_info.get("no_flights") and origin_info.get("iata"):
                    flights = get_cheap_flights(
                        origin_info["iata"], dest_info["iata"],
                        target_date, m["days_range"]
                    )
                    for f in flights:
                        if f["price"] <= m["threshold"]:
                            hits.append({
                                "origin": origin_name.title(),
                                "type": "✈️",
                                "source": "Aviasales",
                                "price": f["price"],
                                "detail": f"📅 {f['date']}  {f['airline']} {f['flight_number']}",
                                "link": "",
                            })

                # Поезда
                trains = get_cheap_trains(
                    origin_info["rzd_code"], dest_info["rzd_code"],
                    target_date, m["days_range"]
                )
                for t in trains:
                    if t["min_price"] <= m["threshold"]:
                        hits.append({
                            "origin": origin_name.title(),
                            "type": "🚂",
                            "source": "РЖД",
                            "price": t["min_price"],
                            "detail": f"📅 {t['date']}  №{t['train']}  🕐 {t['departure']}→{t['arrival']}",
                            "link": "",
                        })

            if not hits:
                continue

            hits.sort(key=lambda x: x["price"])
            best = hits[0]
            origins_str = ", ".join(o.title() for o in m["origins"])

            msg_lines = [
                f"🔔 *Мониторинг #{m['id']} сработал!*",
                f"Маршрут: {origins_str} → {m['destination'].title()}",
                f"Дата: {m['travel_date']} (±{m['days_range']} дн.)",
                f"Порог: {m['threshold']:,} ₽  |  Найдено: *{best['price']:,} ₽* ({best['type']} из {best['origin']})",
                "",
                "*Все варианты ниже порога:*",
            ]
            for h in hits[:8]:
                link = f" [→ купить]({h['link']})" if h.get("link") else ""
                msg_lines.append(
                    f"  {h['type']} *{h['price']:,} ₽* [{h['source']}] из {h['origin']}  {h['detail']}{link}"
                )

            msg_lines.append("\n_Мониторинг остаётся активным до команды /stop_")

            await bot.send_message(
                chat_id=m["chat_id"],
                text="\n".join(msg_lines),
                parse_mode="Markdown",
            )
            await mark_notified(m["id"])

        except Exception as e:
            logger.error(f"Ошибка в мониторинге #{m['id']}: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_monitors,
        trigger="interval",
        hours=CHECK_INTERVAL_HOURS,
        args=[bot],
        id="check_monitors",
        replace_existing=True,
    )
    return scheduler
