import locale


def parse_es_float(value) -> float:
    return float(value.replace(".", "").replace(",", "."))


def format_es_float(value: float) -> str:
    return locale.format_string("%.2f", value, True, True)
