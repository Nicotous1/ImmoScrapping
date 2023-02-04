# %%
%load_ext autoreload
%autoreload 2

import pandas as pd
from pathlib import Path
from immo_scrap import analysis, nexity, histories, mails

SCRAP_FOLDER = Path("../downloads/")
snaps_df = nexity.load_scrapping_folder_to_snapshot_df_list(SCRAP_FOLDER)


# %%
history_snaps_df = histories.create_short_history_from_iterable_and_newest_as_current(snaps_df)

# %%
global_analysis = analysis.create_GlobalAnalysis_from_history_snaps(history_snaps_df)
# %%
mails.send_analysis_if_sold_or_new(global_analysis)