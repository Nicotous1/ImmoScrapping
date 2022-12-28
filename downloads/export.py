from pathlib import Path
from immo_scrap import nexity

if __name__ == "__main__":
    folder_path = Path(".")
    print("Running...")
    nexity.export_biens_from_scrapping_folder_to_std_parquet(folder_path)
    print("Done.")
