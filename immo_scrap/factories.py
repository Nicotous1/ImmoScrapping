from datetime import datetime
import factory
from factory import fuzzy
from . import nexity


def FuzzyBoolean():
    return fuzzy.FuzzyChoice([True, False])


class NexityBienFactory(factory.Factory):
    class Meta:
        model = nexity.NexityBien

    id = factory.Sequence(str)
    type = fuzzy.FuzzyChoice(nexity.BienType)
    price = fuzzy.FuzzyFloat(10, 900_000, precision=0)
    price_low_tva = None
    date_livraison = "3ème trimestre 2025"
    size = fuzzy.FuzzyInteger(20, 60)
    floor = fuzzy.FuzzyInteger(0, 20)
    orientation = fuzzy.FuzzyChoice(nexity.Orientation)
    has_balcony = FuzzyBoolean()
    has_terasse = FuzzyBoolean()
    n_parking = fuzzy.FuzzyInteger(0, 4)
    n_pieces = fuzzy.FuzzyText()
    date_loaded = fuzzy.FuzzyNaiveDateTime(start_dt=datetime(2020, 1, 1))
