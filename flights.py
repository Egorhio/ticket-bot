"""
Поиск дешёвых авиабилетов через Aviasales Data API (Travelpayouts).
Данные кэшированы до 48ч — отражают реальные цены из поиска пользователей.
Документация: https://support.travelpayouts.com/hc/en-us/articles/203956163
"""

import requests
from datetime import date, timedelta
from config import AVIASALES_TOKEN
from cities import find_city

BASE_URL = "https://api.travelpayouts.com"
AVIASALES_SEARCH = "https://www.aviasales.ru/search"


def make_aviasales_link(origin: str, dest: str, date_str: str) -> str:
    """Ссылка на поиск Aviasales: MOW + 0807 + KZN + 1 пассажир."""
    try:
        d = date.fromisoformat(date_str)
        day_month = d.strftime("%d%m")
    except ValueError:
        day_month = ""
    return f"{AVIASALES_SEARCH}/{origin}{day_month}{dest}1"


def get_cheap_flights(
    origin: str,
    destination: str,
    target_date: date,
    days_range: int = 2,
) -> list[dict]:
    """
    Возвращает список самых дешёвых рейсов в диапазоне target_date ± days_range.

    Каждый элемент: {"date": str, "price": int, "transfers": int,
                      "airline": str, "flight_number": str, "departure_at": str}
    """
    if not AVIASALES_TOKEN:
        return []

    month_str = target_date.strftime("%Y-%m")
    url = f"{BASE_URL}/v1/prices/calendar"
    params = {
        "origin": origin,
        "destination": destination,
        "depart_date": month_str,
        "currency": "rub",
        "token": AVIASALES_TOKEN,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    if not data.get("success"):
        return []

    results = []
    raw = data.get("data", {})

    start = target_date - timedelta(days=days_range)
    end = target_date + timedelta(days=days_range)

    for date_str, info in raw.items():
        try:
            flight_date = date.fromisoformat(date_str)
        except ValueError:
            continue
        if not (start <= flight_date <= end):
            continue

        results.append({
            "date": date_str,
            "price": info.get("price", 0),
            "transfers": info.get("transfers", 0),
            "airline": info.get("airline", "—"),
            "flight_number": info.get("flight_number", "—"),
            "departure_at": info.get("departure_at", "—"),
            "link": make_aviasales_link(origin, destination, date_str),
        })

    results.sort(key=lambda x: x["price"])
    return results


def format_flights(flights: list[dict], origin_label: str = "") -> str:
    prefix = f" из {origin_label}" if origin_label else ""
    if not flights:
        return f"✈️ Авиарейсы{prefix} не найдены"

    lines = [f"✈️ *Авиабилеты{prefix}* (Aviasales, кэш до 48ч):"]
    for f in flights[:5]:
        stops = "прямой" if f["transfers"] == 0 else f"{f['transfers']} пересадка(и)"
        link = f" [🛒 купить]({f['link']})" if f.get("link") else ""
        lines.append(
            f"  📅 {f['date']}  💰 *{f['price']:,} ₽*  {stops}  {f['airline']} {f['flight_number']}{link}"
        )
    return "\n".join(lines)


def compare_flights(
    origins: list[tuple[str, str]],  # [(display_name, iata), ...]
    dest_iata: str,
    target_date,
    days_range: int,
) -> str:
    """
    Ищет авиабилеты из нескольких городов и возвращает сравнительный отчёт.
    origins: список кортежей (название для отображения, IATA-код)
    """
    if not AVIASALES_TOKEN:
        return "✈️ Авиабилеты: токен Aviasales не задан (добавьте AVIASALES_TOKEN в .env)"

    results_by_origin: dict[str, list[dict]] = {}
    for display, iata in origins:
        if not iata:
            results_by_origin[display] = []
            continue
        flights = get_cheap_flights(iata, dest_iata, target_date, days_range)
        results_by_origin[display] = flights

    # Находим лучшую цену по всем городам
    best: dict[str, int | None] = {
        name: (flights[0]["price"] if flights else None)
        for name, flights in results_by_origin.items()
    }
    valid_prices = {k: v for k, v in best.items() if v is not None}

    lines = ["✈️ *Авиабилеты — сравнение по городу отправления* (кэш Aviasales):"]

    for display, flights in results_by_origin.items():
        info = find_city(display)
        if info and info.get("no_flights"):
            lines.append(f"\n📍 *{display.title()}* — нет регулярных рейсов")
            continue
        if not flights:
            lines.append(f"\n📍 *{display.title()}* — рейсы не найдены")
            continue
        cheapest = flights[0]
        stops = "прямой" if cheapest["transfers"] == 0 else f"{cheapest['transfers']} пересадка(и)"
        link = f"  [🛒 купить]({cheapest['link']})" if cheapest.get("link") else ""
        lines.append(
            f"\n📍 *{display.title()}*"
            f"\n  Лучшая цена: 💰 *{cheapest['price']:,} ₽*  📅 {cheapest['date']}  {stops}"
            f"\n  {cheapest['airline']} {cheapest['flight_number']}{link}"
        )

    if len(valid_prices) > 1:
        winner = min(valid_prices, key=lambda k: valid_prices[k])
        loser = max(valid_prices, key=lambda k: valid_prices[k])
        diff = valid_prices[loser] - valid_prices[winner]
        lines.append(
            f"\n🏆 *Выгоднее лететь из {winner.title()}* — дешевле на {diff:,} ₽"
        )

    return "\n".join(lines)
