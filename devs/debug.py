# %%
%load_ext autoreload
%autoreload 2
from datetime import date, datetime
from pathlib import Path
from typing import List

from matplotlib.pyplot import ylim
import pandas as pd
from immo_scrap import aws, nexity, analysis, tasks
analysis.set_display_format_for_amount_with_separator()

# %%

folder = Path("../downloads/debug")
tasks.scrap_and_download_from_s3_history(folder)

# %%
snaps = nexity.load_scrapping_folder_to_snapshot_df_list(folder)
