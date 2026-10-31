type Scalar = str | int | float | bool | None


_NULLISH_VALUES = frozenset({"", "n/a", "na", "nan", "null"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "t", "y", "enabled"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off", "f", "n", "disabled"})


def normalize_nullable(value: Scalar) -> Scalar:
    if isinstance(value, str):
        normalized_value = value.strip()
        return (
            None if normalized_value.casefold() in _NULLISH_VALUES else normalized_value
        )

    return value


def convert_to_optional_float(value: Scalar) -> float | None:
    normalized_value = normalize_nullable(value)
    if normalized_value is None:
        return None

    return float(normalized_value)


def convert_to_optional_int(value: Scalar) -> int | None:
    normalized_value = normalize_nullable(value)
    if normalized_value is None:
        return None

    return int(float(normalized_value))


def convert_int_to_optional_bool(value: Scalar) -> bool | None:
    normalized_value = normalize_nullable(value)
    if normalized_value is None:
        return None

    text_value = str(normalized_value).casefold()
    if text_value in _TRUE_VALUES:
        return True

    if text_value in _FALSE_VALUES:
        return False

    try:
        return bool(int(float(text_value)))
    except ValueError:
        return None
