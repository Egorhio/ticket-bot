"""
Поиск авиабилетов через Aviasales Flight Search API (real-time).
В отличие от Data API — не кэш, а живые цены на момент запроса.

Доступ: тот же AVIASALES_TOKEN, но нужно отдельно запросить доступ к Search API
через Travelpayouts → Инструменты → API → "Aviasales Flight Search API"
Документация: https://support.travelpayouts.com/hc/en-us/articles/30565016140434

ВАЖНО: Search API имеет двухшаговый процесс:
  1. POST /v1/search — инициировать поиск, получить search_id
  2. GET  /v1/search/results — опросить результаты (polling)
  Мы делаем несколько попыток с паузой.
"""

import time
import requests
import logging
from datetime import date, timedelta
from config import AVIASALES_TOKEN

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.travelpayouts.com/v1/search"
RESULTS_URL = "https://api.travelpayouts.com/v1/search/results"

AIRLINE_NAMES = {
    "DP": "Победа",
    "SU": "Аэрофлот",
    "S7": "S7",
    "U6": "Уральские авиалинии",
    "UT": "Utair",
    "5N": "Nordwind",
    "N4": "Nordstar",
    "FV": "Россия",
    "ZF": "Азимут",
    "IO": "IrAero",
    "YC": "ЮВТ АЭРО",
}


def _airline_label(code: str) -> str:
    return AIRLINE_NAMES.get(code, code)


def get_realtime_flights(
    origin_iata: str,
    dest_iata: str,
    target_date: date,
    days_range: int = 2,
) -> list[dict]:
    """
    Real-time поиск через Aviasales Search API.
    Возвращает список: {"date", "price", "airline", "transfers",
                         "departure", "arrival"}
    Возвращает [] если Search API не доступен (используется только Data API).
    """
    if not AVIASALES_TOKEN:
        return []

    results = []
    for delta in range(-days_range, days_range + 1):
        search_date = target_date + timedelta(days=delta)
        flights = _search_one_date(origin_iata, dest_iata, search_date)
        results.extend(flights)

    results.sort(key=lambda x: x["price"])
    return results


def _search_one_date(origin: str, dest: str, search_date: date) -> list[dict]:
    """Поиск на конкретную дату через Search API."""
    payload = {
        "marker": "",          # заполнится при наличии партнёрского marker-а
        "host": "localhost",
        "user_ip": "127.0.0.1",
        "locale": "ru",
        "trip_class": "Y",
        "passengers": {"adults": 1, "children": 0, "infants": 0},
        "segments": [
            {
                "origin": origin,
                "destination": dest,
                "date": search_date.strftime("%Y-%m-%d"),
            }
        ],
    }
    headers = {
        "X-Access-Token": AVIASALES_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(SEARCH_URL, json=payload, headers=headers, timeout=10)
        if resp.status_code == 403:
            # Search API не подключён — тихо возвращаем []
            return []
        resp.raise_for_status()
        search_id = resp.json().get("search_id")
        if not search_id:
            return []
    except Exception:
        return []

    # Polling результатов (до 3 попыток с паузой 2 сек)
    for attempt in range(3):
        time.sleep(2)
        try:
            r = requests.get(
                RESULTS_URL,
                params={"uuid": search_id, "token": AVIASALES_TOKEN},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            continue

        proposals = data.get("proposals", [])
        if not proposals:
            continue

        out = []
        for p in proposals[:5]:
            price = p.get("terms", {})
            # Минимальная цена из всех вариантов оплаты
            min_price = min(
                (v.get("price", {}).get("total_price", 999999) for v in price.values()),
                default=None,
            )
            if not min_price:
                continue

            segment = p.get("segment", [{}])[0]
            flights_in_seg = segment.get("flight", [{}])
            first = flights_in_seg[0] if flights_in_seg else {}
            last = flights_in_seg[-1] if flights_in_seg else {}

            out.append({
                "date": search_date.isoformat(),
                "price": int(min_price),
                "airline": _airline_label(first.get("operating_carrier", "—")),
                "transfers": len(flights_in_seg) - 1,
                "departure": first.get("local_departure_timestamp", "")[:5] or "—",
                "arrival": last.get("local_arrival_timestamp", "")[:5] or "—",
            })
        return sorted(out, key=lambda x: x["price"])

    return []


def format_realtime(flights: list[dict], origin_label: str = "") -> str:
    """Форматирует результаты real-time поиска."""
    prefix = f" из {origin_label}" if origin_label else ""
    if not flights:
        return ""   # Пустая строка — Search API не доступен, не показывать блок

    lines = [f"⚡ *Aviasales real-time{prefix}* (живые цены):"]
    for f in flights[:5]:
        stops = "прямой" if f["transfers"] == 0 else f"{f['transfers']} пересадка(и)"
        lines.append(
            f"  📅 {f['date']}  💰 *{f['price']:,} ₽*  {f['airline']}  "
            f"🕐 {f['departure']}→{f['arrival']}  {stops}"
        )
    return "\n".join(lines)


def compare_kiwi(
    origins: list[tuple[str, str]],
    dest_iata: str,
    target_date: date,
    days_range: int,
) -> str:
    """Сравнивает real-time цены из нескольких городов."""
    results_by_origin: dict[str, list[dict]] = {}
    for display, iata in origins:
        if iata:
            results_by_origin[display] = get_realtime_flights(iata, dest_iata, target_date, days_range)

    # Если ни один origin не вернул данные — Search API не подключён
    if not any(results_by_origin.values()):
        return ""

    valid = {k: v[0]["price"] for k, v in results_by_origin.items() if v}
    lines = ["⚡ *Aviasales real-time — сравнение:*"]

    for display, flights in results_by_origin.items():
        if not flights:
            lines.append(f"\n📍 *{display.title()}* — не найдено")
            continue
        f = flights[0]
        stops = "прямой" if f["transfers"] == 0 else f"{f['transfers']} пересадка(и)"
        lines.append(
            f"\n📍 *{display.title()}*"
            f"\n  💰 *{f['price']:,} ₽*  {f['airline']}  📅 {f['date']}  {stops}"
        )

    if len(valid) > 1:
        winner = min(valid, key=lambda k: valid[k])
        loser = max(valid, key=lambda k: valid[k])
        diff = valid[loser] - valid[winner]
        lines.append(f"\n🏆 *Выгоднее из {winner.title()}* — дешевле на {diff:,} ₽")

    return "\n".join(lines)
