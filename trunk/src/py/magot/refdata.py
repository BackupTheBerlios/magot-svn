from peak.model.elements import Immutable, Struct
from peak.model.enumerations import Enumeration, enum
from peak.model.features import structField
from datetime import date

from magot.fixedpoint import FixedPoint


class Date(Immutable):

    def mdl_fromString(klass, value):
        return date.fromtimestamp(value)

    def mdl_toString(klass, value):
        return str(value)


class Currency(Enumeration):

    USD = enum()
    EUR = enum()


class Money(Struct):

    """Immutable Money type containing amount and currency."""

    class amount(structField):
        referencedType = FixedPoint
        defaultValue = FixedPoint('0')

    class currency(structField):
        referencedType = Currency
        defaultValue = Currency.EUR
    
    def __init__(self, amount=0, currency=Currency.EUR):
        super(Money, self).__init__(amount=FixedPoint(amount, 2), currency=currency)
    
    def __add__(self, other):
        assert isinstance(other, Money)
        return Money(
            amount = self.amount + other.amount, 
            currency = self.currency
        )
    
    def __sub__(self, other):
        assert isinstance(other, Money)
        return Money(
            amount = self.amount - other.amount, 
            currency=self.currency
        )
    
    def __str__(self):
        return "%s %s" % (self.amount, self.currency)

    def __nonzero__(self):
        return self.amount <>0

    def mdl_normalize(klass, value):
        return value

    def mdl_fromFields(klass, fieldSeq):
        """Return a new instance from a sequence of fields"""
        return klass()
    
    def mdl_fromString(klass, value):
        return klass(amount=FixedPoint(value))

    def mdl_toString(klass, value):
        return value.amount + value.currency

Money.Zero = Money()

class MovementType(Enumeration):

    CREDIT = enum()
    DEBIT = enum()
