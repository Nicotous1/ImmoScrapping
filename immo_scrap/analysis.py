from dataclasses import dataclass
from enum import Enum
from itertools import tee
from pathlib import Path
from typing import (Dict, Generic, Iterable, List, Set, Tuple, TypedDict,
                    TypeVar)

import pandas as pd
from traitlets import Any

T = TypeVar("T")


def set_display_format_for_amount_with_separator() -> None:
    pd.options.display.float_format = "{:,.2f}".format


def pairwise(iterable: Iterable[T]) -> Iterable[Tuple[T, T]]:
    # pairwise('ABCDEFG') --> AB BC CD DE EF FG
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def compute_periods_stats_by_bien(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("id")["date_loaded"]
    return pd.concat(
        [
            g.min().rename("date_loaded_start"),
            g.max().rename("date_loaded_end"),
            g.nunique().rename("N_loading"),
        ],
        axis=1,
    )


def compute_price_stats_by_bien(df: pd.DataFrame) -> pd.DataFrame:
    g = df.sort_values("date_loaded").groupby("id")["price"]
    return pd.concat(
        [
            g.first().rename("price_start"),
            g.last().rename("price_end"),
            g.std().round(2).rename("price_std"),
        ],
        axis=1,
    )


def extract_biens_infos_by_bien(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.sort_values("date_loaded", ascending=True)
        .drop_duplicates(subset=["id"], keep="last")
        .set_index("id", verify_integrity=True)[
            ["type", "n_pieces", "size", "floor", "orientation"]
        ]
    )


def build_analysis_df_for_each_bien(biens: pd.DataFrame) -> pd.DataFrame:
    res = pd.concat(
        [
            extract_biens_infos_by_bien(biens),
            compute_price_stats_by_bien(biens),
            compute_periods_stats_by_bien(biens),
        ],
        axis=1,
    )
    return res


from datetime import date, datetime

from immo_scrap import histories


@dataclass
class SnapshotDF:
    df: pd.DataFrame
    date: date


def sort_snapshot_dfs_by_oldest_first(dfs: List[SnapshotDF]) -> List[SnapshotDF]:
    return list(sorted(dfs, key=lambda x: x.date))


SNAP_HISTORY = histories.ShortHistory[SnapshotDF]


def select_snapshot(df: pd.DataFrame, dt: datetime) -> pd.DataFrame:
    selector = df["date_loaded"] == dt
    return df[selector]


T = TypeVar("T")


@dataclass
class BiensCompareSnap(Generic[T]):
    current: date
    previous: date
    sold: T
    new: T
    remaining: T


@dataclass
class StatSnap:
    date: date
    n: int


def select_idxs(df: pd.DataFrame, idxs: Iterable) -> pd.DataFrame:
    selector = df["id"].isin(idxs)
    return df.loc[selector]


BiensCompareSnapDF = BiensCompareSnap[pd.DataFrame]
BiensCompareSnapN = BiensCompareSnap[int]


def create_BiensCompareSnap_from_two_snap_df(
    current: SnapshotDF, previous: SnapshotDF
) -> BiensCompareSnapDF:
    idxs_previous = set(previous.df["id"])
    idxs_current = set(current.df["id"])

    idxs_new = idxs_current.difference(idxs_previous)
    idxs_sold = idxs_previous.difference(idxs_current)
    idxs_remaining = idxs_current.intersection(idxs_current)

    df_new = select_idxs(current.df, idxs_new)
    df_sold = select_idxs(previous.df, idxs_sold)
    df_remaining = select_idxs(current.df, idxs_remaining)

    return BiensCompareSnap(current.date, previous.date, df_sold, df_new, df_remaining)


def create_BiensCompareSnapN_from_BiensCompareSnapDF(
    dfs: BiensCompareSnapDF,
) -> BiensCompareSnapN:
    return BiensCompareSnap(
        current=dfs.current,
        previous=dfs.previous,
        sold=dfs.sold.shape[0],
        new=dfs.new.shape[0],
        remaining=dfs.remaining.shape[0],
    )


def create_StatSnap_from_SnapDF(snap_df: SnapshotDF) -> StatSnap:
    return StatSnap(snap_df.date, n=snap_df.df.shape[0])


def check_if_compare_int_has_evolved(compare: BiensCompareSnap[int]) -> bool:
    return compare.sold > 0 or compare.new > 0


@dataclass
class GlobalAnalysis:
    stat_history: histories.ShortHistory[StatSnap]
    previous_compare_df: BiensCompareSnap[pd.DataFrame]
    previous_compare_N: BiensCompareSnap[int]

    @property
    def has_evolved(self) -> bool:
        return check_if_compare_int_has_evolved(self.previous_compare_N)


def format_GlobalAnalysis_title(analysis: GlobalAnalysis) -> str:
    return f"Nexity - {analysis.previous_compare_N.sold} vente / {analysis.previous_compare_N.new} nouveau"


def format_GlobalAnalysis_text(analysis: GlobalAnalysis) -> str:
    current_date = analysis.stat_history.current.date
    res = f"Global Analysis at {format_date(current_date)}\n\n"
    res += f"{format_stat_history_N(analysis.stat_history)}\n\n"
    res += f"{format_compare_N_and_DF(analysis.previous_compare_N, analysis.previous_compare_df)}"
    return res


def format_stat_history_N(history: histories.ShortHistory[StatSnap]) -> str:
    res = f"Historique du nombre de biens :\n"
    res += f"\t{format_stat_snap(history.original)}\n"
    res += f"\t{format_stat_snap(history.previous)}\n"
    res += f"\t{format_stat_snap(history.current)}\n"
    return res


def format_compare_N_and_DF(
    compare_N: BiensCompareSnap[int], compare_DF: BiensCompareSnap[pd.DataFrame]
) -> str:
    current_snap = compare_N.current
    previous_snap = compare_N.previous
    res = f"Evolutions {format_date(previous_snap)} -> {format_date(current_snap)} :\n"
    sub_res = format_N_and_biens_DF(compare_N.sold, compare_DF.sold, name="vente")
    sub_res += format_N_and_biens_DF(compare_N.new, compare_DF.new, name="nouveau")
    sub_res += f"{compare_N.remaining} restants\n"
    res += add_indent(sub_res)
    return res


def format_price(p: float) -> str:
    return f"{p:,.2f} €"


def format_bien_series(bien: pd.Series) -> str:
    res = f"Lot {bien['id']} ; {bien['size']}M² / {bien['n_pieces']} / {bien['orientation']} / Etage {bien['floor']} / Prix {format_price(bien['price'])}"
    if bien["price_low_tva"] is None:
        res += " / Pas de TVA 5.5"
    else:
        res += f" / TVA 5.5 {format_price(bien['price_low_tva'])}"
    return res


def format_biens_dataframes(df: pd.DataFrame) -> str:
    res = ""
    for _, row in df.iterrows():
        res += f"{format_bien_series(row)}\n"
    return res


def format_N_and_biens_DF(N: int, biens: pd.DataFrame, name: str) -> str:
    if N == 0:
        return f"0 {name}\n"
    else:
        res = f"{N} {name} :\n"
        res += add_indent(format_biens_dataframes(biens)) + "\n"
        return res


def add_indent(s: str) -> str:
    s = "\t" + s
    s = s.replace("\n", "\n\t")
    if s.endswith("\t"):
        s = s[:-2]
    return s


def format_stat_snap(stat: StatSnap) -> str:
    return f"{format_date(stat.date)} -> {stat.n} biens"


def format_date(dt: date) -> str:
    return f"{dt:%Y/%m/%d}"


def create_GlobalAnalysis_from_history_snaps(history: SNAP_HISTORY) -> GlobalAnalysis:
    if history.previous is None:
        raise ValueError("Previous shoudl exist for global analysis")
    previous_compare_df = create_BiensCompareSnap_from_two_snap_df(
        history.current, history.previous
    )
    previous_compare_N = create_BiensCompareSnapN_from_BiensCompareSnapDF(
        previous_compare_df
    )
    stat_history = create_StatHistory_from_DFHistory(history)
    return GlobalAnalysis(stat_history, previous_compare_df, previous_compare_N)


def create_StatHistory_from_DFHistory(
    history: SNAP_HISTORY,
) -> histories.ShortHistory[StatSnap]:
    return histories.ShortHistory(
        current=create_StatSnap_from_SnapDF(history.current),
        previous=(
            create_StatSnap_from_SnapDF(history.previous) if history.previous else None
        ),
        original=create_StatSnap_from_SnapDF(history.original),
    )


class EventType(Enum):
    SOLD = "SOLD"
    PUBLISH = "PUBLISH"


@dataclass
class Event:
    bien_id: str
    date: date
    type: EventType


def create_event_from_series_date_and_type(
    row: pd.Series, date: date, type: EventType
) -> Event:
    return Event(bien_id=row["id"], date=date, type=type)


def create_events_of_type_with_date_from_df(
    df: pd.DataFrame, date: date, type: EventType
) -> List[Event]:
    return [
        create_event_from_series_date_and_type(row, date, type)
        for _, row in df.iterrows()
    ]


def create_sold_events_from_df_at_date(df: pd.DataFrame, date: date) -> List[Event]:
    return create_events_of_type_with_date_from_df(df, date, EventType.SOLD)


def create_publish_events_from_df_at_date(df: pd.DataFrame, date: date) -> List[Event]:
    return create_events_of_type_with_date_from_df(df, date, EventType.PUBLISH)


def create_events_from_two_snaps_df(
    current: SnapshotDF, previous: SnapshotDF
) -> List[Event]:
    compare = create_BiensCompareSnap_from_two_snap_df(current, previous)
    return create_events_from_compare_snap_at_date(current.date, compare)


def create_events_from_compare_snap_at_date(now: date, compare: BiensCompareSnap):
    sold_events = create_sold_events_from_df_at_date(compare.sold, now)
    publish_events = create_publish_events_from_df_at_date(compare.new, now)
    events = sold_events + publish_events
    return events


def create_events_from_df_snaps(datas: List[SnapshotDF]) -> List[Event]:
    datas_sorted = sort_snapshot_dfs_by_oldest_first(datas)
    events = create_events_from_df_snaps_oldest_first(datas_sorted)
    return events


def create_events_from_df_snaps_oldest_first(
    datas_sorted: List[SnapshotDF],
) -> List[Event]:
    events = []
    for previous, current in pairwise(datas_sorted):
        events_i = create_events_from_two_snaps_df(current, previous)
        events += events_i
    return events


class EventRecord(TypedDict):
    id: str
    type: str
    date: datetime


def convert_date_to_midnight_datetime(date: date) -> datetime:
    return datetime.combine(date, datetime.min.time())


def create_record_from_event(event: Event) -> EventRecord:
    return {
        "id": event.bien_id,
        "type": event.type.value,
        "date": convert_date_to_midnight_datetime(event.date),
    }


def convert_events_to_dataframe(events: List[Event]) -> pd.DataFrame:
    records = [create_record_from_event(event) for event in events]
    return pd.DataFrame.from_records(records)


def get_columnsnames_of_df_except_lists(
    df: pd.DataFrame, to_filter: Iterable[str]
) -> Set[str]:
    columns = set(df.columns)
    for col_to_filter in to_filter:
        columns.remove(col_to_filter)
    return columns


def merge_snapshot_dfs_to_get_all_versions(datas: List[SnapshotDF]) -> pd.DataFrame:
    datas_sorted = sort_snapshot_dfs_by_oldest_first(datas)
    dfs_merged = concat_snapshots_dfs_to_one_df_with_snapshot(datas_sorted)
    dfs_unique = remove_dupplicate_bien_of_df(dfs_merged)
    return dfs_unique


def remove_dupplicate_bien_of_df(
    dfs_merged: pd.DataFrame,
) -> pd.DataFrame:
    cols_to_check_for_dupplicate = ["id", "price"]
    dfs_unique = dfs_merged.drop_duplicates(
        subset=cols_to_check_for_dupplicate, keep="first"
    )
    return dfs_unique


def select_id_of_df(df: pd.DataFrame, id: str) -> pd.DataFrame:
    return df.loc[df["id"] == id]


def select_ids_of_df_sorted_by_snapshot(
    df: pd.DataFrame, ids: List[str]
) -> pd.DataFrame:
    df = select_ids_of_df(df, ids)
    df = df.sort_values(["id", "SNAPSHOT_DATE"], ascending=True)
    return df


def select_ids_of_events(df: pd.DataFrame, ids: List[str]) -> pd.DataFrame:
    df = select_ids_of_df(df, ids)
    df = df.sort_values(["id", "date"], ascending=True)
    return df

def extract_ids_with_more_than_two_event_from_events_df(df:pd.DataFrame)->List[str]:
    counts = count_ids_dupplicate_with_bigger_first(df)
    counts_more_than_2 = counts.loc[counts > 2]
    ids = list(counts_more_than_2.index.values)
    return ids

def select_ids_of_df(df: pd.DataFrame, ids: List[str]) -> pd.DataFrame:
    selector = df["id"].isin(ids)
    df = df.loc[selector]
    return df


def concat_snapshots_dfs_to_one_df_with_snapshot(
    datas_sorted: List[SnapshotDF],
) -> pd.DataFrame:
    dfs_to_merge: List[pd.DataFrame] = []
    for data in datas_sorted:
        df_i = data.df.copy()
        df_i["SNAPSHOT_DATE"] = convert_date_to_midnight_datetime(data.date)
        dfs_to_merge.append(df_i)
    dfs_merged = pd.concat(dfs_to_merge, axis=0)
    return dfs_merged


def count_ids_dupplicate_with_bigger_first(df: pd.DataFrame) -> pd.Series:
    s = df["id"].value_counts().sort_values(ascending=False).rename("N")
    return s.loc[s > 1].copy()
