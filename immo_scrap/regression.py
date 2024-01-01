import pandas as pd
from sklearn.linear_model import LinearRegression


def preproc_snapshot_df_to_regression_df(df:pd.DataFrame)->pd.DataFrame:
    COLS_FLOAT = ["size", "floor"]
    COLS_TO_KEEP = ["SNAPSHOT_DATE", "price"]
    df_to_keep = df[COLS_FLOAT + COLS_TO_KEEP]
    COLS_CAT = ["orientation"]
    df_dummies = pd.get_dummies(df[COLS_CAT])
    df_reg = pd.concat([df_to_keep, df_dummies], axis=1)
    assert df.shape[0] == df_reg.shape[0]
    return df_reg

def get_coef_series_from_reg(reg:LinearRegression, df_reg:pd.DataFrame)->pd.Series:
    return pd.Series(list(reg.coef_) + [reg.intercept_], index=(list(df_reg.columns) + ["Constant"]))

def compute_regression_coef_for_df_reg(df_reg:pd.DataFrame)->pd.Series:
    X = df_reg.drop("price", axis=1)
    reg = LinearRegression().fit(X, df_reg["price"])
    coefs = get_coef_series_from_reg(reg, X)
    return coefs

def compute_regression_coef_by_snapshot_from_df_history(df_history:pd.DataFrame)->pd.DataFrame:
    df_reg = preproc_snapshot_df_to_regression_df(df_history)
    return df_reg.groupby("SNAPSHOT_DATE").apply(compute_regression_coef_for_df_reg)

def plot_regression_coefs(coefs:pd.DataFrame)->None:
    coefs[["size", "floor"]].plot(ylim=0)
    

def extract_price_m2_for_each_snapshot_by_biens(df:pd.DataFrame)->pd.Series:
    snapshots = df["SNAPSHOT_DATE"].unique()
    df["price_m2"] = df["price"] / df["size"]
    
    def f_apply(df:pd.DataFrame)->pd.DataFrame:
        s = df[["SNAPSHOT_DATE", "price_m2"]].set_index("SNAPSHOT_DATE")["price_m2"].reindex(snapshots)
        return s.sort_index().fillna(method="ffill").fillna(method="bfill").to_frame()
    return df.groupby("id").apply(f_apply).groupby("SNAPSHOT_DATE")["price_m2"].mean()

def plot_price_m2_by_snapshot(prices:pd.Series)->None:
    prices.plot(ylim=(6000, 6400))