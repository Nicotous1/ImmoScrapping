from dataclasses import dataclass
import dataclasses
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Union
import pandas as pd
from bs4 import BeautifulSoup, ResultSet, Tag
import requests


def extract_tables_from_soup(soup: BeautifulSoup) -> ResultSet:
    return soup.select(".product--lots-details .content")


def extract_table_header(table: Tag) -> Tag:
    return table.select(".content--header")[0]


def extract_title_from_table(table: Tag) -> str:
    header = extract_table_header(table)
    return header.select("strong")[0].text.strip()


def extract_n_theoric_from_table(table: Tag) -> int:
    header = extract_table_header(table)
    text_dispo = header.select(".text--dispo")[0].text.strip()
    n_dispo_str = text_dispo.split(" ")[0]
    n_dispo_int = int(n_dispo_str)
    return n_dispo_int


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
    APPARTEMENT = "Appartement"


class Orientation(Enum):
    NORTH_WEST = "Nord-Ouest"
    SOUTH_EAST = "Sud-Est"
    SOUTH_WEST = "Sud-Ouest"


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
        return convert_price_str_to_float(datas[key]) if key in datas else None

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
    columns = extract_columns_name_from_table(table)
    values = extract_elements_values_from_table(table)
    res = [
        NexityLine.create_from_dict(dict(zip(columns, values_i))) for values_i in values
    ]
    return res


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
    def create_from_nexity_table(cls, table: NexityTable) -> List["NexityBien"]:
        return [
            NexityBien(
                date_loaded=datetime.now(), n_pieces=table.n_pieces, **bien.__dict__
            )
            for bien in table.biens
        ]


def convert_nexity_biens_to_dataframe(biens: List[NexityBien]) -> pd.DataFrame:
    biens_dict = [bien.__dict__ for bien in biens]
    df = pd.DataFrame.from_records(biens_dict)
    cols_enum = ["type", "orientation"]
    for col_enum in cols_enum:
        df[col_enum] = df[col_enum].apply(lambda x: x.value)
    return df


def extract_nexity_biens_from_soup(soup: BeautifulSoup) -> List[NexityBien]:
    tables = extract_nexity_tables_from_soup(soup)
    biens = []
    for table in tables:
        nexity_biens_i = NexityBien.create_from_nexity_table(table)
        biens += nexity_biens_i
    return biens


def save_nexity_biens_to_parquet(biens: List[NexityBien], path: Path) -> None:
    df = convert_nexity_biens_to_dataframe(biens)
    df.to_parquet(path)
