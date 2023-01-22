from pathlib import Path

from immo_scrap import aws

html_folder = Path("../downloads")
aws.sync_html_from_folder_to_nexity_bucket(html_folder)