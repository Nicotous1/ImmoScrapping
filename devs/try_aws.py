# %%
from pathlib import Path

from immo_scrap import aws

name = "nexity-web-scrapping"
bucket = aws.load_bucket(name)

# %%
backup_folder = Path("C:\\Users\\ntous\\Desktop\\Codes\\ImmoScrapping\\devs")
bucket.upload_folder_files_missing_from_root(backup_folder)

#%%
#%%
folder = Path("C:\\Users\\ntous\\Desktop\\Codes\\ImmoScrapping\\devs")
bucket.download_all_to_folder(folder)

#%%
file = Path(
    "C:\\Users\\ntous\\Desktop\\Codes\\ImmoScrapping\\downloads\\signal_2023_01_22.html"
)

bucket.upload_to_root(file)

# %%
