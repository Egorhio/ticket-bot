"""
Поиск билетов на поезд через неофициальный API pass.rzd.ru.
Двухшаговый процесс: POST → получить rid, GET с rid → получить данные.
"""

import time
import requests
from datetime import date, timedelta

BASE_URL = "https://pass.rzd.ru/timetable/public/ru"
RZD_ORDER_URL = "https://pass.rzd.ru/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://pass.rzd.ru/",
}

# Слои: 5827 = расписание с ценами
LAYER_ID = 5827


def make_rzd_link(from_code: int, to_code: int, travel_date: date) -> str:
    """Ссылка на покупку билетов — страница поиска pass.rzd.ru с параметрами."""
    dt = travel_date.strftime("%d.%m.%Y")
    return (
        f"{RZD_ORDER_URL}?STRUCTURE_ID=735&layer_id=5371"
        f"&dir=0&tfl=3&checkSeats=1&code0={from_code}&dt0={dt}&code1={to_code}"
    )


def _fetch_rid(session: requests.Session, from_code: int, to_code: int, travel_date: date) -> str | None:
    """Шаг 1: POST-запрос для получения rid."""
    params = {
        "layer_id": LAYER_ID,
        "dir": 0,
        "tfl": 3,
        "checkSeats": 1,
        "code0": from_code,
        "code1": to_code,
        "dt0": travel_date.strftime("%d.%m.%Y"),
        "md": 0,
    }
    try:
        resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("RID")  # ключ с заглавной буквы в ответе РЖД
    except Exception:
        return None


def _fetch_trains(session: requests.Session, rid: str) -> list[dict]:
    """Шаг 2: GET по rid для получения поездов."""
    params = {"layer_id": LAYER_ID, "rid": rid}
    for _ in range(5):
        time.sleep(1.5)
        try:
            resp = session.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("result") == "RID":
                continue
            return data.get("tp", [{}])[0].get("list", [])
        except Exception:
            break
    return []


def get_cheap_trains(
    from_code: int,
    to_code: int,
    target_date: date,
    days_range: int = 2,
) -> list[dict]:
    """
    Ищет поезда в диапазоне target_date ± days_range.
    Возвращает список: {"date": str, "train": str, "departure": str,
                        "arrival": str, "travel_time": str,
                        "min_price": int, "car_type": str}
    """
    session = requests.Session()
    try:
        session.get("https://pass.rzd.ru/", headers=HEADERS, timeout=10)
    except Exception:
        pass
    results = []

    dates = [target_date + timedelta(days=d) for d in range(-days_range, days_range + 1)]

    for travel_date in dates:
        rid = _fetch_rid(session, from_code, to_code, travel_date)
        if not rid:
            continue

        trains = _fetch_trains(session, rid)
        for train in trains:
            cars = train.get("cars", [])
            if not cars:
                continue

            # Находим минимальную цену по всем вагонам
            prices = []
            best_car_type = "—"
            for car in cars:
                price = car.get("tariff", 0)
                if price:
                    if not prices or price < min(prices):
                        best_car_type = car.get("typeLoc", "—")
                    prices.append(price)

            if not prices:
                continue

            results.append({
                "date": travel_date.strftime("%Y-%m-%d"),
                "train": train.get("number", "—"),
                "brand": train.get("brand", ""),
                "departure": train.get("time0", "—"),
                "arrival": train.get("time1", "—"),
                "travel_time": train.get("timeInWay", "—"),
                "min_price": min(prices),
                "car_type": best_car_type,
                "link": make_rzd_link(from_code, to_code, travel_date),
            })

    results.sort(key=lambda x: x["min_price"])
    return results


def format_trains(trains: list[dict], origin_label: str = "") -> str:
    prefix = f" из {origin_label}" if origin_label else ""
    if not trains:
        return f"🚂 Поезда{prefix} не найдены"

    lines = [f"🚂 *Поезда РЖД{prefix}* (pass.rzd.ru):"]
    for t in trains[:5]:
        brand = f" «{t['brand']}»" if t["brand"] else ""
        link = f"  [🛒 купить]({t['link']})" if t.get("link") else ""
        lines.append(
            f"  📅 {t['date']}  💰 *{t['min_price']:,} ₽* ({t['car_type']}){link}\n"
            f"     №{t['train']}{brand}  🕐 {t['departure']}→{t['arrival']}  ⏱ {t['travel_time']}"
        )
    return "\n".join(lines)


def compare_trains(
    origins: list[tuple[str, int]],  # [(display_name, rzd_code), ...]
    dest_code: int,
    target_date,
    days_range: int,
) -> str:
    """
    Ищет поезда из нескольких городов и возвращает сравнительный отчёт.
    origins: список кортежей (название для отображения, код РЖД)
    """
    results_by_origin: dict[str, list[dict]] = {}
    for display, code in origins:
        trains = get_cheap_trains(code, dest_code, target_date, days_range)
        results_by_origin[display] = trains

    best: dict[str, int | None] = {
        name: (trains[0]["min_price"] if trains else None)
        for name, trains in results_by_origin.items()
    }
    valid_prices = {k: v for k, v in best.items() if v is not None}

    lines = ["🚂 *Поезда РЖД — сравнение по городу отправления* (pass.rzd.ru):"]

    for display, trains in results_by_origin.items():
        if not trains:
            lines.append(f"\n📍 *{display.title()}* — поезда не найдены")
            continue
        t = trains[0]
        brand = f" «{t['brand']}»" if t["brand"] else ""
        link = f"  [🛒 купить]({t['link']})" if t.get("link") else ""
        lines.append(
            f"\n📍 *{display.title()}*"
            f"\n  Лучшая цена: 💰 *{t['min_price']:,} ₽* ({t['car_type']}){link}"
            f"\n  №{t['train']}{brand}  📅 {t['date']}  🕐 {t['departure']}→{t['arrival']}"
        )

    if len(valid_prices) > 1:
        winner = min(valid_prices, key=lambda k: valid_prices[k])
        loser = max(valid_prices, key=lambda k: valid_prices[k])
        diff = valid_prices[loser] - valid_prices[winner]
        lines.append(
            f"\n🏆 *Выгоднее ехать из {winner.title()}* — дешевле на {diff:,} ₽"
        )

    return "\n".join(lines)
