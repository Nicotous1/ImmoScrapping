# %%
from datetime import date
from pathlib import Path

from immo_scrap import aws, nexity

current = nexity.NexityFile(Path("."), date(2023, 1, 22))
nexity_bucket = aws.create_nexity_bucket()
history = aws.create_history_from_s3_bucket_and_current_file(nexity_bucket, current)
