import pytest

from src.ingest.formatting import (
    convert_int_to_optional_bool,
    convert_to_optional_float,
    convert_to_optional_int,
    normalize_nullable,
)


class TestNormalizeNullable:
    def test_none_returns_none(self) -> None:
        assert normalize_nullable(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert normalize_nullable("") is None

    def test_na_string_returns_none(self) -> None:
        assert normalize_nullable("N/A") is None

    def test_nan_string_returns_none(self) -> None:
        assert normalize_nullable("NaN") is None

    def test_null_string_returns_none(self) -> None:
        assert normalize_nullable("null") is None

    def test_valid_string_returns_stripped(self) -> None:
        assert normalize_nullable("  Intel Core i7  ") == "Intel Core i7"

    def test_valid_string_unchanged(self) -> None:
        assert normalize_nullable("Host") == "Host"

    def test_zero_string_returns_zero(self) -> None:
        assert normalize_nullable("0") == "0"


class TestToOptionalFloat:
    def test_scientific_notation(self) -> None:
        result = convert_to_optional_float("4.022910e-05")
        assert result == pytest.approx(4.02291e-05)

    def test_plain_number(self) -> None:
        assert convert_to_optional_float("37.04") == pytest.approx(37.04)

    def test_na_returns_none(self) -> None:
        assert convert_to_optional_float("N/A") is None

    def test_none_returns_none(self) -> None:
        assert convert_to_optional_float(None) is None

    def test_empty_returns_none(self) -> None:
        assert convert_to_optional_float("") is None


class TestToOptionalInt:
    def test_integer_string(self) -> None:
        assert convert_to_optional_int("10") == 10

    def test_float_string_truncates(self) -> None:
        assert convert_to_optional_int("100000.0") == 100000

    def test_na_returns_none(self) -> None:
        assert convert_to_optional_int("N/A") is None

    def test_none_returns_none(self) -> None:
        assert convert_to_optional_int(None) is None


class TestToOptionalBoolFromInt:
    def test_one_returns_true(self) -> None:
        assert convert_int_to_optional_bool("1") is True

    def test_zero_returns_false(self) -> None:
        assert convert_int_to_optional_bool("0") is False

    def test_na_returns_none(self) -> None:
        assert convert_int_to_optional_bool("N/A") is None

    def test_none_returns_none(self) -> None:
        assert convert_int_to_optional_bool(None) is None

    def test_false_string_returns_false(self) -> None:
        # TNL's CUDA metadata reports e.g. "GPU memory ECC enabled": "false"
        assert convert_int_to_optional_bool("false") is False

    def test_true_string_returns_true(self) -> None:
        assert convert_int_to_optional_bool("true") is True

    def test_mixed_case_and_yes_no(self) -> None:
        assert convert_int_to_optional_bool("False") is False
        assert convert_int_to_optional_bool("YES") is True
        assert convert_int_to_optional_bool("no") is False

    def test_unparseable_raises(self) -> None:
        with pytest.raises(ValueError):
            convert_int_to_optional_bool("maybe")
