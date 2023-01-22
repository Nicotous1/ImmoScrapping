# %%
from pathlib import Path

from immo_scrap import tasks

SCRAP_FOLDER = Path("../downloads/")
# %%
tasks.download_analyse_send_mail_if_needed_and_save_to_s3(SCRAP_FOLDER)
