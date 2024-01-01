# %%
%load_ext autoreload
%autoreload 2
from datetime import date, datetime
from pathlib import Path
from typing import List

from matplotlib.pyplot import ylim
import pandas as pd
from immo_scrap import regression, analysis, nexity
analysis.set_display_format_for_amount_with_separator()

# # %%
# DOWNLOAD_FOLDER = Path("../downloads/")
# datas = nexity.load_scrapping_folder_to_snapshot_df_list(DOWNLOAD_FOLDER)

# # %%
# df_history = analysis.concat_snapshots_dfs_to_one_df_with_snapshot(datas)
# df_history.to_parquet("dfs_history.parquet")

# %%
df_history = pd.read_parquet("dfs_history.parquet")
df_history

# %%
regs_coeffs = regression.compute_regression_coef_by_snapshot_from_df_history(df_history)
regression.plot_regression_coefs(regs_coeffs)
