from pathlib import Path
from immo_scrap import nexity

if __name__ == "__main__":
    folder_path = Path(".")
    nexity.download_and_save_signal_html(folder_path)
