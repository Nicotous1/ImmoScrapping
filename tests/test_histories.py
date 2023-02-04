import random
from dataclasses import dataclass
from datetime import date
from unittest.mock import MagicMock

import pytest

from immo_scrap import histories


@dataclass
class DatedObject:
    date: date


def create_date_object(dt: date):
    return DatedObject(date=dt)


@pytest.mark.parametrize(
    "previous, dt, next, expected",
    [
        (date(2000, 1, 1), date(2010, 1, 1), date(2020, 1, 1), True),
        (date(2010, 1, 1), date(2010, 1, 1), date(2020, 1, 1), False),
        (date(2020, 1, 1), date(2010, 1, 1), date(2020, 1, 1), False),
        (date(2009, 1, 1), date(2010, 1, 1), date(2010, 1, 1), False),
    ],
)
def test_check_is_dt_strictly_between(
    dt: date, previous: date, next: date, expected: bool
):
    res = histories.check_if_dt_strictly_between(dt, previous, next)
    assert res is expected


@pytest.mark.parametrize(
    "dt",
    [(create_date_object(date(2000, 1, 1))), (create_date_object(date(2005, 1, 1)))],
)
def test_select_if_older_than_keep_source_when_same_or_older(dt):
    source = create_date_object(date(2000, 1, 1))
    res = histories.select_if_older_than(dt, source)
    assert source is res


def test_select_if_older_than_keep_to_check_if_strictly_older():
    source = create_date_object(date(2000, 1, 1))
    dt = create_date_object(date(1999, 1, 1))
    res = histories.select_if_older_than(dt, source)
    assert dt is res


def test_select_if_previous_than_keep_none_if_previous_none_and_not_older_than_current():
    previous = None
    current = create_date_object(date(2000, 1, 1))
    dt = create_date_object(date(2001, 1, 1))
    res = histories.select_if_previous_than(dt, previous, current)
    assert res is None


def test_select_if_previous_than_keep_dt_if_previous_none_and_older_than_current():
    previous = None
    current = create_date_object(date(2000, 1, 1))
    dt = create_date_object(date(1999, 1, 1))
    res = histories.select_if_previous_than(dt, previous, current)
    assert res is dt


def test_select_if_previous_than_keep_dt_if_older_than_current_and_previous():
    current = create_date_object(date(2000, 1, 1))
    previous = create_date_object(date(1999, 1, 1))
    dt = create_date_object(date(1998, 1, 1))
    res = histories.select_if_previous_than(dt, previous, current)
    assert res is previous


def test_select_if_previous_than_keep_dt_if_previous_and_older_than_current_but_not_previous():
    current = create_date_object(date(2000, 1, 1))
    previous = create_date_object(date(1999, 1, 1))
    dt = create_date_object(date(1999, 12, 1))
    res = histories.select_if_previous_than(dt, previous, current)
    assert res is dt


def test_select_if_previous_than_keep_dt_if_previous_and_not_older_than_current():
    current = create_date_object(date(2000, 1, 1))
    previous = create_date_object(date(1999, 1, 1))
    dt = create_date_object(date(2001, 12, 1))
    res = histories.select_if_previous_than(dt, previous, current)
    assert res is previous


def test_create_short_history_from_iterable():
    current = create_date_object(date(2020, 12, 25))
    original = create_date_object(date(2018, 12, 24))
    previous = create_date_object(date(2020, 12, 24))
    items = [
        original,
        create_date_object(date(2019, 11, 23)),
        create_date_object(date(2019, 12, 23)),
        previous,
        create_date_object(date(2020, 12, 25)),
    ]
    random.shuffle(items)
    expected = histories.ShortHistory(current, previous, original)
    res = histories.create_short_history_from_iterable(current, items)
    assert res == expected


def test_create_short_history_from_iterable_with_no_items():
    current = create_date_object(date(2020, 12, 25))
    items = []
    expected = histories.ShortHistory(current, None, current)
    res = histories.create_short_history_from_iterable(current, items)
    assert res == expected
