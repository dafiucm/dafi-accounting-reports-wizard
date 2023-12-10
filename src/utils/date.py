import datetime


def format_date(date: datetime.date) -> str:
    return date.strftime("%-d de %B de %Y")
