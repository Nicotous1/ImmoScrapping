from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Iterable, List, TypeVar

import pandas as pd


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
