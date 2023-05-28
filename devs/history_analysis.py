# %%
%load_ext autoreload
%autoreload 2
from pathlib import Path
from typing import List
from immo_scrap import aws, nexity, analysis
analysis.set_display_format_for_amount_with_separator()

DOWNLOAD_FOLDER = Path("../downloads/")
# %%
bucket = aws.create_nexity_bucket()
bucket.download_all_to_folder(DOWNLOAD_FOLDER)
# %%
datas = nexity.load_scrapping_folder_to_snapshot_df_list(DOWNLOAD_FOLDER)

# %%
events = analysis.create_events_from_df_snaps(datas)
events_df = analysis.convert_events_to_dataframe(events)
dfs_history = analysis.merge_snapshot_dfs_to_get_all_versions(datas)

# %%
analysis.count_ids_dupplicate_with_bigger_first(events_df)

# %%
IDS_WITH_MULTIPLE_EVENTS = analysis.extract_ids_with_more_than_two_event_from_events_df(events_df)
analysis.select_ids_of_events(events_df, IDS_WITH_MULTIPLE_EVENTS)

# %%
analysis.select_ids_of_df_sorted_by_snapshot(dfs_history, IDS_WITH_MULTIPLE_EVENTS)

# %%
biens_with_evolution = analysis.count_ids_dupplicate_with_bigger_first(dfs_history)
biens_with_evolution

# %%
IDS_WITH_EVOLUTION = list(biens_with_evolution.index.values)
analysis.select_ids_of_df_sorted_by_snapshot(dfs_history, IDS_WITH_EVOLUTION)
