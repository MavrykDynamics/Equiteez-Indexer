"""Exact nonnegative integers without a machine-word or Decimal-context limit."""

from decimal import Decimal
from dipdup.models import fields


class NaturalField(fields.DecimalField):
    # DipDup validates its field registry; register this exact-integer extension
    # below, just as dipdup.fields registers its built-in Tortoise extensions.
    __module__ = fields.__name__
    skip_to_python_if_native = False

    def __init__(self, **kwargs):
        super().__init__(max_digits=78, decimal_places=0, **kwargs)

    SQL_TYPE = "NUMERIC"

    class _db_sqlite:
        # NUMERIC affinity would silently round a large integer through a float.
        SQL_TYPE = "TEXT"

    def to_python_value(self, value):
        if value is None:
            self.validate(value)
            return None
        if isinstance(value, (bool, float)):
            raise ValueError("NaturalField requires an exact integer")
        number = Decimal(value)
        if not number.is_finite() or number < 0 or number != number.to_integral_value():
            raise ValueError("NaturalField requires a nonnegative integer")
        result = number
        self.validate(result)
        return result

    def to_db_value(self, value, instance):
        number = self.to_python_value(value)
        return None if number is None else Decimal(number)


fields.NaturalField = NaturalField
