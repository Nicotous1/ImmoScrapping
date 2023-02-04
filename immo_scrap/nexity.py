import dataclasses
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Union

import pandas as pd
import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from immo_scrap import analysis


def extract_tables_from_soup(soup: BeautifulSoup) -> ResultSet:
    return soup.select(".product--lots-details .content")


def extract_table_header(table: Tag) -> Tag:
    return table.select(".content--header")[0]


def extract_title_from_table(table: Tag) -> str:
    header = extract_table_header(table)
    return header.select("strong")[0].text.strip()


def extract_n_theoric_from_table(table: Tag) -> int:
    header = extract_table_header(table)
    n_dispo_str = header.select(".text--dispo")[0].text
    n_dispo_int = convert_n_theoric_str_to_int(n_dispo_str)
    return n_dispo_int


def convert_n_theoric_str_to_int(s: str) -> int:
    s = s.strip().lower()
    s_splitted = s.split(" ")
    if s.startswith("plus"):
        s_int = s_splitted[2]
    else:
        s_int = s_splitted[0]
    return int(s_int)


def extract_columns_name_from_table(table: Tag) -> List[str]:
    column_name_cells = table.select(".content--details--header .cell")
    columns_name = [cell.text.strip() for cell in column_name_cells]
    columns_name = columns_name[:-1]  # Remove Plan 2D / 3D (download item)
    return columns_name


def extract_elements_from_table(table: Tag) -> ResultSet:
    return table.select(".content--details--element .line")


def extract_cells_text_from_element(element: Tag) -> List[str]:
    cells = element.select(".cell")
    cells_text = [cell.text.strip() for cell in cells]
    cells_text_without_download = cells_text[:-1]  # Remove Plan 2D / 3D (download item)
    return cells_text_without_download


def extract_elements_values_from_table(table: Tag) -> List[List[str]]:
    elements = extract_elements_from_table(table)
    eleemnts_texts = [extract_cells_text_from_element(element) for element in elements]
    return eleemnts_texts


def extract_dataframe_from_table(table: Tag) -> pd.DataFrame:
    columns = extract_columns_name_from_table(table)
    values = extract_elements_values_from_table(table)
    df = pd.DataFrame(
        data=values,
        columns=columns,
    )
    return df


class BienType(Enum):
    STUDIO = "Studio"
    APPARTEMENT = "Appartement"


class Orientation(Enum):
    NORTH_WEST = "Nord-Ouest"
    SOUTH_EAST = "Sud-Est"
    SOUTH_WEST = "Sud-Ouest"
    NORTH_EAST = "Nord-Est"


def convert_price_str_to_float(price: str) -> float:
    price_amount_str = price.replace(" ", "").replace("€", "")
    price_float = float(price_amount_str)
    return price_float


def convert_m2_str_to_int(size: str) -> int:
    size_amount_str = size.replace(" ", "").replace("m²", "")
    size_float = int(size_amount_str)
    return size_float


def convert_floor_str_to_int(etage: str) -> int:
    etage_amount_str = etage[6:]
    etage_float = int(etage_amount_str)
    return etage_float


def convert_n_inclus_str_to_int(n_inclus_str: str) -> int:
    if n_inclus_str == "Non":
        return 0
    else:  # Format '$$ inclus'
        return int(n_inclus_str[:-7])


@dataclass
class NexityLine:
    id: str
    type: BienType
    price: float
    price_low_tva: Union[None, float]
    date_livraison: str
    size: int
    floor: int
    orientation: Orientation
    has_balcony: bool
    has_terasse: bool
    n_parking: int

    @staticmethod
    def extract_type(datas: Dict[str, Any]) -> BienType:
        return BienType(datas["Type"])

    @staticmethod
    def extract_price(datas: Dict[str, Any]) -> float:
        return convert_price_str_to_float(datas["Prix TVA 20%"])

    @staticmethod
    def extract_price_low_tva(datas: Dict[str, Any]) -> Union[None, float]:
        key = "TVA réduite  (2)"
        price_low_tva_str = datas.get(key, "").strip()
        if (price_low_tva_str == "-") | (price_low_tva_str == ""):
            return None
        else:
            return convert_price_str_to_float(price_low_tva_str)

    @staticmethod
    def extract_size(datas: Dict[str, Any]) -> int:
        return convert_m2_str_to_int(datas["Surface"])

    @staticmethod
    def extract_floor(datas: Dict[str, Any]) -> int:
        return convert_floor_str_to_int(datas["Étage"])

    @staticmethod
    def extract_orientation(datas: Dict[str, Any]) -> Orientation:
        return Orientation(datas["Orientation"])

    @staticmethod
    def extract_has_balcony(datas: Dict[str, Any]) -> bool:
        return "Balcon" in datas["Les +"]

    @staticmethod
    def extract_has_terasse(datas: Dict[str, Any]) -> bool:
        return "Terasse" in datas["Les +"]

    @staticmethod
    def extract_date_livraison(datas: Dict[str, Any]) -> str:
        return datas["Livraison"]

    @staticmethod
    def extract_n_parking(datas: Dict[str, Any]) -> int:
        key = "Parking"
        return convert_n_inclus_str_to_int(datas[key]) if key in datas else 0

    @classmethod
    def create_from_dict(cls, datas: Dict[str, Any]):
        return NexityLine(
            id=datas["id"],
            type=cls.extract_type(datas),
            price=cls.extract_price(datas),
            price_low_tva=cls.extract_price_low_tva(datas),
            date_livraison=cls.extract_date_livraison(datas),
            size=cls.extract_size(datas),
            floor=cls.extract_floor(datas),
            orientation=cls.extract_orientation(datas),
            has_balcony=cls.extract_has_balcony(datas),
            has_terasse=cls.extract_has_terasse(datas),
            n_parking=cls.extract_n_parking(datas),
        )


def extract_biens_from_table(table: Tag) -> List[NexityLine]:
    biens_dict = extract_line_dict_from_table(table)
    res = [NexityLine.create_from_dict(bien_dict) for bien_dict in biens_dict]
    return res


def extract_line_dict_from_table(table: Tag) -> List[Dict[str, str]]:
    """Data from the table value but also hidden info like idx"""
    table_dicts = extract_table_dicts_from_table(table)
    add_idxs_to_table_dicts_from_table(table, table_dicts)
    return table_dicts


def extract_table_dicts_from_table(table: Tag) -> List[Dict[str, str]]:
    """Only the value from the table itself"""
    columns = extract_columns_name_from_table(table)
    values = extract_elements_values_from_table(table)
    table_dicts = [(dict(zip(columns, values_i))) for values_i in values]
    return table_dicts


def add_idxs_to_table_dicts_from_table(
    table: Tag, table_dicts: List[Dict[str, str]]
) -> None:
    idxs = extract_table_lot_idxs(table)
    for idx, table_dict in zip(idxs, table_dicts):
        table_dict["id"] = idx


def extract_idx_from_title(title: str) -> str:
    idx_str = title.strip().replace(" ", "")[3:]
    return idx_str


def extract_idx_from_line(line: Tag) -> str:
    first_cell = line.select(".cell")[0]
    first_cell_title: str = first_cell["title"]  # type:ignore
    idx = extract_idx_from_title(first_cell_title)
    return idx


def extract_table_lot_idxs(table: Tag) -> List[str]:
    lines = extract_elements_from_table(table)
    return [extract_idx_from_line(line) for line in lines]


@dataclass
class NexityTable:
    biens: List[NexityLine]
    n_pieces: str
    n_theoric: int

    @classmethod
    def create_from_table_tag(cls, table: Tag) -> "NexityTable":
        biens = extract_biens_from_table(table)
        title = extract_title_from_table(table)
        n_theoric = extract_n_theoric_from_table(table)
        return NexityTable(
            biens=biens,
            n_pieces=title,
            n_theoric=n_theoric,
        )


def extract_nexity_tables_from_soup(soup: BeautifulSoup) -> List[NexityTable]:
    tables = extract_tables_from_soup(soup)
    nexity_tables = [NexityTable.create_from_table_tag(table) for table in tables]
    return nexity_tables


@dataclass
class NexityBien:
    id: str
    type: BienType
    price: float
    price_low_tva: Union[None, float]
    date_livraison: str
    size: int
    floor: int
    orientation: Orientation
    has_balcony: bool
    has_terasse: bool
    n_parking: int
    n_pieces: str
    date_loaded: datetime

    @classmethod
    def create_from_nexity_table_of_date(
        cls, table: NexityTable, date_loaded: datetime
    ) -> List["NexityBien"]:
        return [
            NexityBien(
                date_loaded=date_loaded, n_pieces=table.n_pieces, **bien.__dict__
            )
            for bien in table.biens
        ]


def convert_nexity_biens_to_dataframe(biens: List[NexityBien]) -> pd.DataFrame:
    biens_dict = [bien.__dict__ for bien in biens]
    if len(biens_dict) == 0:
        return pd.DataFrame()
    df = pd.DataFrame.from_records(biens_dict)
    cols_enum = ["type", "orientation"]
    for col_enum in cols_enum:
        df[col_enum] = df[col_enum].apply(lambda x: x.value)
    return df


def extract_nexity_biens_from_soup(
    soup: BeautifulSoup, date_loaded: datetime
) -> List[NexityBien]:
    tables = extract_nexity_tables_from_soup(soup)
    biens = []
    for table in tables:
        nexity_biens_i = NexityBien.create_from_nexity_table_of_date(table, date_loaded)
        biens += nexity_biens_i
    return biens


def save_nexity_biens_to_parquet(biens: List[NexityBien], path: Path) -> None:
    df = convert_nexity_biens_to_dataframe(biens)
    df.to_parquet(path)


def download_content_from_url(url: str) -> bytes:
    return requests.get(url).content


def create_beautiful_soup_from_html_bytes(data: bytes) -> BeautifulSoup:
    return BeautifulSoup(data, features="html.parser")


def download_soup_from_url(url: str) -> BeautifulSoup:
    res = download_content_from_url(url)
    soup = create_beautiful_soup_from_html_bytes(res)
    return soup


def download_soup_from_file(file: Path) -> BeautifulSoup:
    res = read_bytes_from(file)
    soup = create_beautiful_soup_from_html_bytes(res)
    return soup


def download_nexity_biens_from_url(url: str) -> List[NexityBien]:
    soup = download_soup_from_url(url)
    date_loaded = datetime.now()
    biens = extract_nexity_biens_from_soup(soup, date_loaded)
    return biens


def download_and_save_nexity_biens_from_url(url: str, path: Path) -> None:
    biens = download_nexity_biens_from_url(url)
    save_nexity_biens_to_parquet(biens, path)


NEXITY_FILE_PREFIX = "signal_"


def generate_signal_stem_for_date(dt: date) -> str:
    return f"{NEXITY_FILE_PREFIX}{dt:%Y_%m_%d}"


def generate_signal_html_filename_for_dt(dt: date) -> str:
    stem = generate_signal_stem_for_date(dt)
    file_name = f"{stem}.html"
    return file_name


def extract_date_from_signal_stem(stem: str) -> date:
    date_str = stem[len(NEXITY_FILE_PREFIX) :]
    return datetime.strptime(date_str, "%Y_%m_%d").date()


def extract_date_from_signal_html_file(name: str) -> date:
    stem = name[:-5]
    return extract_date_from_signal_stem(stem)


def generate_today() -> date:
    return datetime.now().date()


def create_NexityFile_for_today_and_folder(folder: Path) -> "NexityFile":
    today = generate_today()
    return create_NexityFile_from_dt_and_folder(today, folder)


def create_NexityFile_from_dt_and_folder(dt: date, folder: Path) -> "NexityFile":
    file = folder / generate_signal_html_filename_for_dt(dt)
    return NexityFile(file, dt)


def save_bytes_to(content: bytes, path: Path) -> None:
    f = open(path, "wb")
    f.write(content)
    f.close()


def read_bytes_from(path: Path) -> bytes:
    f = open(path, "rb")
    content = f.read()
    f.close()
    return content


SIGNAL_URL = "https://www.nexity.fr/neuf/0099__98124"


def download_signal_content() -> bytes:
    return download_content_from_url(SIGNAL_URL)


def download_and_save_url_html(url: str, path: Path) -> None:
    content = download_content_from_url(url)
    save_bytes_to(content, path)


def download_and_save_signal_html(folder: Path) -> "NexityFile":
    file = create_NexityFile_for_today_and_folder(folder)
    download_and_save_url_html(SIGNAL_URL, file.path)
    return file


def extract_date_loaded_from_file(file: Path) -> datetime:
    date_str = file.stem[-10:]
    date_loaded = datetime.strptime(date_str, "%Y_%m_%d")
    return date_loaded


def load_biens_from_file_loaded_at(
    file: Path, date_loaded: datetime
) -> List[NexityBien]:
    print(f"Loading biens from {file.name} extracted at {date_loaded}...")
    soup = download_soup_from_file(file)
    biens = extract_nexity_biens_from_soup(soup, date_loaded)
    print("Done")
    return biens


def load_biens_from_scrapped_file(file: Path) -> List[NexityBien]:
    date_loaded = extract_date_loaded_from_file(file)
    biens = load_biens_from_file_loaded_at(file, date_loaded)
    return biens


def load_snapshot_df_from_scrapped_file(file: Path) -> analysis.SnapshotDF:
    date_loaded = extract_date_loaded_from_file(file)
    biens = load_biens_from_file_loaded_at(file, date_loaded)
    biens_df = convert_nexity_biens_to_dataframe(biens)
    return analysis.SnapshotDF(biens_df, date_loaded.date())


def check_if_file_has_ext(file: Path, ext: str) -> bool:
    return file.suffix.lower() == f".{ext}"


def extract_files_of_ext_from_folder(folder: Path, ext: str) -> List[Path]:
    res = []
    for file in folder.iterdir():
        if file.is_file() and check_if_file_has_ext(file, ext):
            res.append(file)
    return res


def extract_html_files_from_folder(folder: Path) -> List[Path]:
    return extract_files_of_ext_from_folder(folder, "html")


def load_biens_from_scrapping_folder(folder: Path) -> List[NexityBien]:
    res = []
    for file in extract_html_files_from_folder(folder):
        res += load_biens_from_scrapped_file(file)
    return res


def save_parquet(df: pd.DataFrame, file: Path) -> None:
    n_rows, n_columns = df.shape
    print(
        f"Saving to parquet {n_rows:,.0f} rows with {n_columns:,.0f} columns at {file.name}"
    )
    df.to_parquet(file)


def export_biens_from_scrapping_folder_to_parquet(
    scrapping_folder: Path, parquet_file: Path
) -> None:
    biens_df = load_scrapping_folder_to_dataframe(scrapping_folder)
    save_parquet(biens_df, parquet_file)


def load_scrapping_folder_to_dataframe(scrapping_folder: Path) -> pd.DataFrame:
    biens = load_biens_from_scrapping_folder(scrapping_folder)
    biens_df = convert_nexity_biens_to_dataframe(biens)
    return biens_df


def load_scrapping_folder_to_snapshot_df_list(
    scrapping_folder: Path,
) -> List[analysis.SnapshotDF]:
    res = []
    for file in extract_html_files_from_folder(scrapping_folder):
        res.append(load_snapshot_df_from_scrapped_file(file))
    return res


def export_biens_from_scrapping_folder_to_std_parquet(scrapping_folder: Path) -> None:
    parquet_file = scrapping_folder / "export.parquet"
    export_biens_from_scrapping_folder_to_parquet(scrapping_folder, parquet_file)


@dataclass
class NexityFile:
    path: Path
    date: date
