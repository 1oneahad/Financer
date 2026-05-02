from datetime import date


def is_positive_int(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def is_positive_amount(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def looks_like_date(value):
    return isinstance(value, str) and len(value.strip()) == 10 and value.count("-") == 2


def parse_date(value):
    return date.fromisoformat(str(value))


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_limit(value, default=100, minimum=1, maximum=500):
    try:
        limit = int(value or default)
    except ValueError:
        return None, "limit must be a number"

    if limit < minimum or limit > maximum:
        return None, f"limit must be between {minimum} and {maximum}"

    return limit, None
