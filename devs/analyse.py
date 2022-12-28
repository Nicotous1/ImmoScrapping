# %%
%load_ext autoreload
%autoreload 2

import pandas as pd
from pathlib import Path
from immo_scrap import analysis

path_export = Path("..\downloads\export.parquet")
biens = pd.read_parquet(path_export)

# %%
analysis_by_biens = analysis.build_analysis_df_for_each_bien(biens)
analysis_by_biens
# %%
