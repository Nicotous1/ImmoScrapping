from pathlib import Path

from immo_scrap import aws

html_folder = Path("../downloads")
aws.upload_new_htmls_to_nexity_bucket(html_folder)
