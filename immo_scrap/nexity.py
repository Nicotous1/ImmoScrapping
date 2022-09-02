from dataclasses import dataclass
from typing import List
import pandas as pd
from bs4 import BeautifulSoup, ResultSet, Tag


def extract_tables_from_soup(soup: BeautifulSoup) -> ResultSet:
    return soup.select(".product--lots-details .content")


def extract_table_header(table: Tag) -> Tag:
    return table.select(".content--header")[0]


def extract_title_from_table(table: Tag) -> str:
    header = extract_table_header(table)
    return header.select("strong")[0].text


def extract_n_theoric_from_table(table: Tag) -> int:
    header = extract_table_header(table)
    text_dispo = header.select(".text--dispo")[0].text.strip()
    n_dispo_str = text_dispo.split(" ")[0]
    n_dispo_int = int(n_dispo_str)
    return n_dispo_int


def extract_columns_name_from_table(table: Tag) -> List[str]:
    column_name_cells = table.select(".content--details--header .cell")
    columns_name = [cell.text for cell in column_name_cells]
    columns_name = columns_name[:-1]  # Remove Plan 2D / 3D (download item)
    return columns_name


def extract_elements_from_table(table: Tag) -> ResultSet:
    return table.select(".content--details--element .line")


def extract_cells_text_from_element(element: Tag) -> List[str]:
    cells = element.select(".cell")
    cells_text = [cell.text for cell in cells]
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


@dataclass
class NexityTable:
    df: pd.DataFrame
    title: str
    n_theoric: int

    @classmethod
    def create_from_table_tag(cls, table: Tag) -> "NexityTable":
        df = extract_dataframe_from_table(table)
        title = extract_title_from_table(table)
        n_theoric = extract_n_theoric_from_table(table)
        return NexityTable(
            df=df,
            title=title,
            n_theoric=n_theoric,
        )


def extract_nexity_tables_from_soup(soup: BeautifulSoup) -> List[NexityTable]:
    tables = extract_tables_from_soup(soup)
    nexity_tables = [NexityTable.create_from_table_tag(table) for table in tables]
    return nexity_tables
