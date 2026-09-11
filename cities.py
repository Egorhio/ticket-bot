"""
Справочник городов: название → IATA-код (авиа) и код станции РЖД.
Коды станций РЖД: https://pass.rzd.ru (числовые expresscodes)
Пометка no_flights=True: в городе нет регулярных коммерческих рейсов.
"""

CITIES: dict[str, dict] = {
    # --- Крупные хабы ---
    "москва": {"iata": "MOW", "rzd_code": 2000000, "rzd_name": "МОСКВА"},
    "санкт-петербург": {"iata": "LED", "rzd_code": 2004000, "rzd_name": "С-ПЕТЕРБУРГ"},
    "питер": {"iata": "LED", "rzd_code": 2004000, "rzd_name": "С-ПЕТЕРБУРГ"},
    "спб": {"iata": "LED", "rzd_code": 2004000, "rzd_name": "С-ПЕТЕРБУРГ"},
    "казань": {"iata": "KZN", "rzd_code": 2060600, "rzd_name": "КАЗАНЬ"},
    "сочи": {"iata": "AER", "rzd_code": 2060400, "rzd_name": "СОЧИ"},
    "екатеринбург": {"iata": "SVX", "rzd_code": 2000006, "rzd_name": "ЕКАТЕРИНБУРГ"},
    "екб": {"iata": "SVX", "rzd_code": 2000006, "rzd_name": "ЕКАТЕРИНБУРГ"},
    "новосибирск": {"iata": "OVB", "rzd_code": 2060300, "rzd_name": "НОВОСИБИРСК"},
    "краснодар": {"iata": "KRR", "rzd_code": 2060200, "rzd_name": "КРАСНОДАР"},
    "нижний новгород": {"iata": "GOJ", "rzd_code": 2060100, "rzd_name": "НИЖНИЙ НОВГОРОД"},
    "нн": {"iata": "GOJ", "rzd_code": 2060100, "rzd_name": "НИЖНИЙ НОВГОРОД"},
    "самара": {"iata": "KUF", "rzd_code": 2060500, "rzd_name": "САМАРА"},
    "уфа": {"iata": "UFA", "rzd_code": 2060700, "rzd_name": "УФА"},
    "ростов": {"iata": "ROV", "rzd_code": 2060800, "rzd_name": "РОСТОВ-НА-ДОНУ"},
    "ростов-на-дону": {"iata": "ROV", "rzd_code": 2060800, "rzd_name": "РОСТОВ-НА-ДОНУ"},
    "пермь": {"iata": "PEE", "rzd_code": 2000005, "rzd_name": "ПЕРМЬ"},
    "воронеж": {"iata": "VOZ", "rzd_code": 2000002, "rzd_name": "ВОРОНЕЖ"},
    "иркутск": {"iata": "IKT", "rzd_code": 2060900, "rzd_name": "ИРКУТСК"},
    "владивосток": {"iata": "VVO", "rzd_code": 2007000, "rzd_name": "ВЛАДИВОСТОК"},
    "хабаровск": {"iata": "KHV", "rzd_code": 2007100, "rzd_name": "ХАБАРОВСК"},
    "красноярск": {"iata": "KJA", "rzd_code": 2061000, "rzd_name": "КРАСНОЯРСК"},
    "тюмень": {"iata": "TJM", "rzd_code": 2000007, "rzd_name": "ТЮМЕНЬ"},
    "омск": {"iata": "OMS", "rzd_code": 2061100, "rzd_name": "ОМСК"},
    "барнаул": {"iata": "BAX", "rzd_code": 2061200, "rzd_name": "БАРНАУЛ"},
    "владикавказ": {"iata": "OGZ", "rzd_code": 2006800, "rzd_name": "ВЛАДИКАВКАЗ"},
    "минеральные воды": {"iata": "MRV", "rzd_code": 2006700, "rzd_name": "МИНЕРАЛЬНЫЕ ВОДЫ"},
    "мвд": {"iata": "MRV", "rzd_code": 2006700, "rzd_name": "МИНЕРАЛЬНЫЕ ВОДЫ"},
    "симферополь": {"iata": "SIP", "rzd_code": 2006000, "rzd_name": "СИМФЕРОПОЛЬ"},
    "калининград": {"iata": "KGD", "rzd_code": 2004100, "rzd_name": "КАЛИНИНГРАД"},
    "архангельск": {"iata": "ARH", "rzd_code": 2004200, "rzd_name": "АРХАНГЕЛЬСК"},
    "мурманск": {"iata": "MMK", "rzd_code": 2004300, "rzd_name": "МУРМАНСК"},
    "волгоград": {"iata": "VOG", "rzd_code": 2006100, "rzd_name": "ВОЛГОГРАД"},
    "астрахань": {"iata": "ASF", "rzd_code": 2006200, "rzd_name": "АСТРАХАНЬ"},
    "саратов": {"iata": "RTW", "rzd_code": 2000003, "rzd_name": "САРАТОВ"},
    "оренбург": {"iata": "REN", "rzd_code": 2000004, "rzd_name": "ОРЕНБУРГ"},
    "челябинск": {"iata": "CEK", "rzd_code": 2000008, "rzd_name": "ЧЕЛЯБИНСК"},
    "тула": {"iata": "TUL", "rzd_code": 2000001, "rzd_name": "ТУЛА"},

    # --- Ивановская область и соседи ---
    "иваново": {"iata": "IWA", "rzd_code": 2003900, "rzd_name": "ИВАНОВО"},
    "ярославль": {"iata": "IAR", "rzd_code": 2003700, "rzd_name": "ЯРОСЛАВЛЬ"},
    "ярл": {"iata": "IAR", "rzd_code": 2003700, "rzd_name": "ЯРОСЛАВЛЬ"},
    "кострома": {"iata": None, "rzd_code": 2003800, "rzd_name": "КОСТРОМА", "no_flights": True},
    "владимир": {"iata": None, "rzd_code": 2001000, "rzd_name": "ВЛАДИМИР", "no_flights": True},
    "вологда": {"iata": "VGD", "rzd_code": 2004500, "rzd_name": "ВОЛОГДА"},
    "рыбинск": {"iata": None, "rzd_code": 2003701, "rzd_name": "РЫБИНСК", "no_flights": True},
    "череповец": {"iata": "CEE", "rzd_code": 2004600, "rzd_name": "ЧЕРЕПОВЕЦ"},

    # --- Поволжье / Центр ---
    "рязань": {"iata": "RZN", "rzd_code": 2001200, "rzd_name": "РЯЗАНЬ"},
    "тверь": {"iata": None, "rzd_code": 2004700, "rzd_name": "ТВЕРЬ", "no_flights": True},
    "калуга": {"iata": "KLF", "rzd_code": 2001100, "rzd_name": "КАЛУГА"},
    "брянск": {"iata": "BZK", "rzd_code": 2001300, "rzd_name": "БРЯНСК"},
    "орёл": {"iata": "OEL", "rzd_code": 2001400, "rzd_name": "ОРЕЛ"},
    "курск": {"iata": "URS", "rzd_code": 2001500, "rzd_name": "КУРСК"},
    "липецк": {"iata": "LPK", "rzd_code": 2001600, "rzd_name": "ЛИПЕЦК"},
    "тамбов": {"iata": "TBW", "rzd_code": 2001700, "rzd_name": "ТАМБОВ"},
    "пенза": {"iata": "PEZ", "rzd_code": 2001800, "rzd_name": "ПЕНЗА"},
    "ульяновск": {"iata": "ULV", "rzd_code": 2001900, "rzd_name": "УЛЬЯНОВСК"},
    "чебоксары": {"iata": "CSY", "rzd_code": 2060601, "rzd_name": "ЧЕБОКСАРЫ"},
    "йошкар-ола": {"iata": "JOK", "rzd_code": 2060602, "rzd_name": "ЙОШКАР-ОЛА"},
    "саранск": {"iata": "SKX", "rzd_code": 2060603, "rzd_name": "САРАНСК"},
    "ижевск": {"iata": "IJK", "rzd_code": 2000010, "rzd_name": "ИЖЕВСК"},
    "киров": {"iata": "KVX", "rzd_code": 2000011, "rzd_name": "КИРОВ"},
}


def find_city(name: str) -> dict | None:
    """Поиск города по названию (нечёткий, без учёта регистра)."""
    key = name.strip().lower()
    if key in CITIES:
        return CITIES[key]
    for city_key, info in CITIES.items():
        if key in city_key or city_key in key:
            return info
    return None


def parse_origins(raw: str) -> list[str]:
    """Разбивает строку вида 'Иваново,Москва,Ярославль' на список имён."""
    return [p.strip() for p in raw.split(",") if p.strip()]


def city_display_name(name: str) -> str:
    """Красивое название города с IATA/пометкой 'без рейсов'."""
    info = find_city(name)
    if not info:
        return name.title()
    label = info["rzd_name"].title()
    if info.get("no_flights"):
        return f"{label} (только поезд)"
    if info.get("iata"):
        return f"{label} ({info['iata']})"
    return label


def list_cities() -> str:
    """Возвращает список всех доступных городов."""
    unique: dict[str, str] = {}
    for info in CITIES.values():
        key = info["rzd_name"]
        if key not in unique:
            suffix = " ✈️🚂" if not info.get("no_flights") and info.get("iata") else " 🚂"
            unique[key] = info["rzd_name"].title() + suffix
    return "\n".join(f"• {v}" for v in sorted(unique.values()))
