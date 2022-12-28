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
