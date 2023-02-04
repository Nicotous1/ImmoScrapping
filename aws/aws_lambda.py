from pathlib import Path

from immo_scrap import tasks


def lambda_handler(event, context):
    print("Start lambda")
    folder = Path("/tmp")
    tasks.download_analyse_send_mail_if_needed_and_save_to_s3(folder)
