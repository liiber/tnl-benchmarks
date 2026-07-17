NULLISH_VALUES = {None, "", "N/A", "n/a", "NA", "na", "nan", "NaN", "null", "NULL"}


def normalize_nullable(value):
    if isinstance(value, str):
        stripped = value.strip()
        return None if stripped in NULLISH_VALUES else stripped
    return None if value in NULLISH_VALUES else value


def to_optional_float(value):
    normalized = normalize_nullable(value)
    return float(normalized) if normalized is not None else None


def to_optional_int(value):
    normalized = normalize_nullable(value)
    return int(float(normalized)) if normalized is not None else None


_TRUE_VALUES = {"1", "true", "yes", "on", "t", "y", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "f", "n", "disabled"}


def to_optional_bool_from_int(value):
    normalized = normalize_nullable(value)
    if normalized is None:
        return None
    text = str(normalized).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    try:
        return bool(int(float(text)))
    except ValueError:
        return None
