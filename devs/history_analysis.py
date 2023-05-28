# %%
%load_ext autoreload # type:ignore
%autoreload 2 # type:ignore
from datetime import date, datetime
from pathlib import Path
from typing import List

from matplotlib.pyplot import ylim
import pandas as pd
from immo_scrap import aws, nexity, analysis
analysis.set_display_format_for_amount_with_separator()

DOWNLOAD_FOLDER = Path("../downloads/")
# %% Fetching data
bucket = aws.create_nexity_bucket()
bucket.download_all_to_folder(DOWNLOAD_FOLDER)
# %%
datas = nexity.load_scrapping_folder_to_snapshot_df_list(DOWNLOAD_FOLDER)

# %%
events = analysis.create_events_from_df_snaps(datas)
events_df = analysis.convert_events_to_dataframe(events)

# %%
dfs_history = analysis.merge_snapshot_dfs_to_get_all_versions(datas)

# %%
IDS_WITH_REPUBLISH = analysis.extract_ids_with_republish_event_from_events_df(events_df)
analysis.select_ids_of_events(events_df, IDS_WITH_REPUBLISH)

# %%
analysis.select_ids_of_df_sorted_by_snapshot(dfs_history, IDS_WITH_REPUBLISH)

# %%
IDS_WITH_EVOLUTION = analysis.get_ids_with_evolution_from_histories(dfs_history)
analysis.select_ids_of_df_sorted_by_snapshot(dfs_history, IDS_WITH_EVOLUTION)

# %%
stocks = analysis.extract_daily_stock_with_forward_fill_from_snapshot_dfs(datas)

# %%
analysis.plot_stocks_over_time(stocks)

# %%
analysis.plot_sell_ratio_over_time(stocks, SELL_RATIO_SHIFT_DAYS=30)

# %%
analysis.plot_selling_speed_over_time(stocks, SELL_RATIO_SHIFT_DAYS=30)
