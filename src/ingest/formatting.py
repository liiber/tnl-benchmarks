type AnyValue = str | int | float | bool | None

NULLISH_VALUES = {None, "", "N/A", "n/a", "NA", "na", "nan", "NaN", "null", "NULL"}


def normalize_nullable(value: AnyValue) -> AnyValue:
    if isinstance(value, str):
        stripped = value.strip()
        return None if stripped in NULLISH_VALUES else stripped
    return value


def convert_to_optional_float(value: AnyValue) -> float | None:
    normalized = normalize_nullable(value)
    return float(normalized) if normalized is not None else None


def convert_to_optional_int(value: AnyValue) -> int | None:
    normalized = normalize_nullable(value)
    return int(float(normalized)) if normalized is not None else None


_TRUE_VALUES = {"1", "true", "yes", "on", "t", "y", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "f", "n", "disabled"}


def convert_int_to_optional_bool(value: AnyValue) -> bool | None:
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
