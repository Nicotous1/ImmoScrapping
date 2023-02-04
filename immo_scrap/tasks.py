from pathlib import Path

from immo_scrap import analysis, aws, histories, mails, nexity


def analyse_and_send_mail_if_needed(folder: Path) -> None:
    print("Analyse")
    snaps_df = nexity.load_scrapping_folder_to_snapshot_df_list(folder)
    history_snaps_df = (
        histories.create_short_history_from_iterable_and_newest_as_current(snaps_df)
    )
    global_analysis = analysis.create_GlobalAnalysis_from_history_snaps(
        history_snaps_df
    )
    print(analysis.format_GlobalAnalysis_title(global_analysis))
    print("Sending mail")
    mails.send_analysis_if_sold_or_new(global_analysis)


def scrap_and_download_from_s3_history(folder: Path) -> None:
    # %% Download new
    current = nexity.download_and_save_signal_html(folder)
    print("Nexity_downloaded")

    # %% Download History
    bucket = aws.create_nexity_bucket()
    history = aws.create_history_from_s3_bucket_and_current_file(bucket, current)
    aws.download_history_previous_and_orignal_to_folder(history, folder)
    print("History downloaded")


def save_to_s3_folder(folder: Path) -> None:
    print("Upload to s3")
    aws.upload_new_htmls_to_nexity_bucket(folder)


def download_analyse_send_mail_if_needed_and_save_to_s3(folder: Path) -> None:
    print("Start task")
    scrap_and_download_from_s3_history(folder)
    analyse_and_send_mail_if_needed(folder)
    save_to_s3_folder(folder)
    print("Done")
