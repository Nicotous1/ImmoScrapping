from dataclasses import dataclass
from datetime import date
from typing import Generic, Iterable, Protocol, TypeVar, Union


class DatedObject(Protocol):
    date: date


T = TypeVar("T")


@dataclass
class ShortHistory(Generic[T]):
    current: T
    previous: Union[None, T]
    original: T


D = TypeVar("D", bound=DatedObject)


def check_if_dt_strictly_between(dt: date, previous: date, next: date) -> bool:
    return previous < dt < next


def check_if_dt_object_strictly_between(dt: D, previous: D, next: D) -> bool:
    return check_if_dt_strictly_between(dt.date, previous.date, next.date)


def select_if_older_than(to_check: D, source: D) -> D:
    if check_if_dt_object_older_than(to_check, source):
        return to_check
    return source


def check_if_dt_object_older_than(dt: D, compare: D) -> bool:
    return dt.date < compare.date


def select_if_previous_than(
    dt: D, previous: Union[None, D], current: D
) -> Union[None, D]:
    no_previous = previous is None
    has_previous = not (no_previous)
    dt_older_than_current = check_if_dt_object_older_than(dt, current)

    if no_previous and dt_older_than_current:
        return dt

    if has_previous and check_if_dt_object_strictly_between(dt, previous, current):
        return dt

    return previous


def create_short_history_from_iterable(
    current: D, items: Iterable[D]
) -> ShortHistory[D]:
    original = current
    previous = None
    for item in items:
        original = select_if_older_than(item, original)
        previous = select_if_previous_than(item, previous, current)
    return ShortHistory(current, previous, original)


def create_short_history_from_iterable_and_newest_as_current(
    items: Iterable[D],
) -> ShortHistory[D]:
    last_item = extract_newest(items)
    return create_short_history_from_iterable(last_item, items)


def select_if_newest_than(dt: D, current: D) -> D:
    if dt.date > current.date:
        return dt
    return current


def extract_newest(items: Iterable[D]) -> D:
    item_max: Union[D, None] = None
    for item in items:
        if item_max is None or (item.date > item_max.date):
            item_max = item
    if item_max is None:
        raise ValueError("Please provide at least one item")
    return item_max
