#!/usr/bin/env python

"""Tests for `immo_scrap` package."""

from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest
import requests
from bs4 import BeautifulSoup, Tag

from immo_scrap import factories, nexity


@pytest.fixture
def nexity_table_tag(nexity_list_soup) -> Tag:
    return nexity.extract_tables_from_soup(nexity_list_soup)[0]


@pytest.fixture
def nexity_table_v2_tag(nexity_list_soup) -> Tag:
    return nexity.extract_tables_from_soup(nexity_list_soup)[1]


@pytest.fixture
def nexity_line_tag(nexity_table_tag) -> Tag:
    return nexity.extract_elements_from_table(nexity_table_tag)[0]


def test_extract_idx_from_line(nexity_line_tag):
    res = nexity.extract_idx_from_line(nexity_line_tag)
    assert res == "4161"


def test_extract_table_lot_idxs(nexity_table_tag):
    res = nexity.extract_table_lot_idxs(nexity_table_tag)
    assert isinstance(res, list)
    assert len(res) == 8
    assert res[:3] == ["4161", "4171", "1122"]


def test_extract_table_from_soup(nexity_list_soup):
    res = nexity.extract_tables_from_soup(nexity_list_soup)
    assert len(res) == 3


def test_extract_title_from_table(nexity_table_tag):
    res = nexity.extract_title_from_table(nexity_table_tag)
    assert res == "2 pièces"


def test_extract_n_theoric_from_table(nexity_table_tag):
    res = nexity.extract_n_theoric_from_table(nexity_table_tag)
    assert isinstance(res, int)
    assert res == 8


@pytest.mark.parametrize(
    "n_theo_str, expected",
    [
        ("8 lots disponibles", 8),
        (" 5 lots disponibles  ", 5),
        ("Plus que 4 lots disponibles !", 4),
    ],
)
def test_convert_n_theoric_str_to_int(n_theo_str, expected):
    res = nexity.convert_n_theoric_str_to_int(n_theo_str)
    assert res == expected


def test_extract_columns_name_from_table(nexity_table_tag):
    res = nexity.extract_columns_name_from_table(nexity_table_tag)
    assert res == [
        "Type",
        "Prix TVA 20%",
        "Livraison",
        "Surface",
        "Étage",
        "Orientation",
        "Les +",
    ]


@pytest.mark.parametrize(
    "input, expected",
    [("Appartement", nexity.BienType.APPARTEMENT), ("Studio", nexity.BienType.STUDIO)],
)
def test_extract_type(input: str, expected):
    datas = {"Type": input}
    res = nexity.NexityLine.extract_type(datas)
    assert res == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("Sud-Ouest", nexity.Orientation.SOUTH_WEST),
        ("Nord-Est", nexity.Orientation.NORTH_EAST),
    ],
)
def test_extract_orientation(input: str, expected):
    datas = {"Orientation": input}
    res = nexity.NexityLine.extract_orientation(datas)
    assert res == expected


def test_extract_columns_name_from_table_v2(nexity_table_v2_tag):
    res = nexity.extract_columns_name_from_table(nexity_table_v2_tag)
    assert res == [
        "Type",
        "TVA réduite  (2)",
        "Prix TVA 20%",
        "Livraison",
        "Surface",
        "Étage",
        "Orientation",
        "Parking",
        "Les +",
    ]


def test_extract_elements_from_table(nexity_table_tag):
    res = nexity.extract_elements_from_table(nexity_table_tag)
    assert isinstance(res, list)
    assert len(res) == 8


@pytest.fixture
def nexity_element_tag(nexity_table_tag):
    res = nexity.extract_elements_from_table(nexity_table_tag)
    return res[0]


def test_extract_cells_text_from_element(nexity_element_tag):
    res = nexity.extract_cells_text_from_element(nexity_element_tag)
    assert res == [
        "Appartement",
        "301 420 €",
        "3ème trimestre 2025",
        "46 m²",
        "Étage 16",
        "Nord-Ouest",
        "",
    ]


def test_extract_dataframe_from_table(nexity_table_tag):
    res = nexity.extract_dataframe_from_table(nexity_table_tag)
    assert isinstance(res, pd.DataFrame)
    assert res.shape == (8, 7)
    expected_row_at_1 = pd.Series(
        [
            "Appartement",
            "303 700 €",
            "3ème trimestre 2025",
            "46 m²",
            "Étage 17",
            "Nord-Ouest",
            "",
        ],
        index=[
            "Type",
            "Prix TVA 20%",
            "Livraison",
            "Surface",
            "Étage",
            "Orientation",
            "Les +",
        ],
        name=1,
    )
    row_at_1 = res.iloc[1]
    pd.testing.assert_series_equal(row_at_1, expected_row_at_1)


class Test_NexityBien:
    @pytest.mark.parametrize(
        "datas, expected",
        [
            (
                {
                    "id": "3",
                    "Type": "Appartement",
                    "Prix TVA 20%": "303 700 €",
                    "Livraison": "3ème trimestre 2025",
                    "Surface": "46 m²",
                    "Étage": "Étage 17",
                    "Orientation": "Nord-Ouest",
                    "Les +": "",
                },
                nexity.NexityLine(
                    id="3",
                    type=nexity.BienType.APPARTEMENT,
                    price=303_700.00,
                    price_low_tva=None,
                    date_livraison="3ème trimestre 2025",
                    size=46,
                    floor=17,
                    orientation=nexity.Orientation.NORTH_WEST,
                    has_balcony=False,
                    has_terasse=False,
                    n_parking=0,
                ),
            ),
            ## Table V2
            (
                {
                    "id": "4",
                    "Type": "Appartement",
                    "TVA réduite  (2)": "493 000 €",
                    "Prix TVA 20%": "560 760 €",
                    "Livraison": "3ème trimestre 2025",
                    "Surface": "88 m²",
                    "Étage": "Étage 1",
                    "Orientation": "Sud-Ouest",
                    "Parking": "1 inclus",
                    "Les +": "Balcon",
                },
                nexity.NexityLine(
                    id="4",
                    type=nexity.BienType.APPARTEMENT,
                    price_low_tva=493_000.00,
                    price=560_760.00,
                    date_livraison="3ème trimestre 2025",
                    size=88,
                    floor=1,
                    orientation=nexity.Orientation.SOUTH_WEST,
                    has_balcony=True,
                    has_terasse=False,
                    n_parking=1,
                ),
            ),
            ## Table V2 avec terasse
            (
                {
                    "id": "1451",
                    "Type": "Appartement",
                    "TVA réduite  (2)": "240 000 €",
                    "Prix TVA 20%": "534 600 €",
                    "Livraison": "3ème trimestre 2025",
                    "Surface": "53 m²",
                    "Étage": "Étage 13",
                    "Orientation": "Sud-Ouest",
                    "Parking": "4 inclus",
                    "Les +": "Terasse",
                },
                nexity.NexityLine(
                    id="1451",
                    type=nexity.BienType.APPARTEMENT,
                    price_low_tva=240_000.00,
                    price=534_600.00,
                    date_livraison="3ème trimestre 2025",
                    size=53,
                    floor=13,
                    orientation=nexity.Orientation.SOUTH_WEST,
                    has_balcony=False,
                    has_terasse=True,
                    n_parking=4,
                ),
            ),
            ## No TVA
            (
                {
                    "Type": "Appartement",
                    "TVA réduite  (2)": "-",
                    "Prix TVA 20%": "327 590 €",
                    "Livraison": "4ème trimestre 2025",
                    "Surface": "48 m²",
                    "Étage": "Étage 16",
                    "Orientation": "Nord-Ouest",
                    "Les +": "",
                    "id": "1162",
                },
                nexity.NexityLine(
                    id="1162",
                    type=nexity.BienType.APPARTEMENT,
                    price_low_tva=None,
                    price=327_590.00,
                    date_livraison="4ème trimestre 2025",
                    size=48,
                    floor=16,
                    orientation=nexity.Orientation.NORTH_WEST,
                    has_balcony=False,
                    has_terasse=False,
                    n_parking=0,
                ),
            ),
        ],
    )
    def test_create_from_dict(self, datas, expected):
        res = nexity.NexityLine.create_from_dict(datas)
        assert res == expected

    def test_create_from_nexity_table_of_date(self, nexity_table):
        now = datetime(2000, 1, 1)
        res = nexity.NexityBien.create_from_nexity_table_of_date(nexity_table, now)
        assert isinstance(res, list)
        assert len(res) == 8
        res_1 = res[1]
        assert isinstance(res_1, nexity.NexityBien)
        assert res_1.n_pieces == nexity_table.n_pieces
        assert res_1.date_loaded == now


@pytest.mark.parametrize(
    "input, expected",
    [
        ("1 inclus", 1),
        ("Non", 0),
        ("13 inclus", 13),
    ],
)
def test_convert_n_inclus_str_to_int(input, expected):
    res = nexity.convert_n_inclus_str_to_int(input)
    assert res == expected


def test_extract_biens_from_table(nexity_table_tag):
    res = nexity.extract_biens_from_table(nexity_table_tag)
    assert isinstance(res, list)
    assert len(res) == 8
    assert isinstance(res[2], nexity.NexityLine)
    assert res[2].id == "1122"


def test_extract_biens_from_table_v2(nexity_table_v2_tag):
    res = nexity.extract_biens_from_table(nexity_table_v2_tag)
    assert isinstance(res, list)
    assert len(res) == 16
    assert isinstance(res[10], nexity.NexityLine)


class Test_NexityTable:
    def test_create_from_table_tag(self, nexity_table_tag):
        res = nexity.NexityTable.create_from_table_tag(nexity_table_tag)
        assert isinstance(res, nexity.NexityTable)
        biens = res.biens
        assert isinstance(biens, list)
        assert len(biens) == 8
        assert isinstance(biens[1], nexity.NexityLine)
        assert res.n_pieces == "2 pièces"
        assert res.n_theoric == 8


@pytest.fixture()
def nexity_table(nexity_table_tag):
    return nexity.NexityTable.create_from_table_tag(nexity_table_tag)


@pytest.fixture()
def nexity_biens(nexity_table):
    return nexity.NexityBien.create_from_nexity_table_of_date(
        nexity_table, datetime(2000, 12, 31)
    )


def test_extract_nexity_tables_from_soup(nexity_list_soup):
    res = nexity.extract_nexity_tables_from_soup(nexity_list_soup)
    assert isinstance(res, list)
    assert len(res) == 3
    res_1 = res[1]
    assert isinstance(res_1, nexity.NexityTable)


def test_convert_nexity_biens_to_dataframe(nexity_biens):
    res = nexity.convert_nexity_biens_to_dataframe(nexity_biens)
    assert isinstance(res, pd.DataFrame)
    assert res.shape == (8, 13)
    assert res.iloc[2]["id"] == "1122"
    assert res.iloc[0]["type"] == "Appartement"
    assert res.iloc[0]["orientation"] == "Nord-Ouest"


def test_extract_nexity_biens_from_soup(nexity_list_soup):
    now = datetime(2013, 3, 1)
    res = nexity.extract_nexity_biens_from_soup(nexity_list_soup, now)
    assert isinstance(res, list)
    assert len(res) == 41
    assert res[0].date_loaded == now


def test_save_nexity_biens(tmp_path: Path):
    file_path = tmp_path / "biens.json"
    biens = factories.NexityBienFactory.create_batch(5)
    nexity.save_nexity_biens_to_parquet(biens, file_path)
    assert file_path.exists() is True
    parquet = pd.read_parquet(file_path)
    assert parquet.shape == (5, 13)


def test_download_soup_from_url(requests_mock):
    url = "http://test.com"
    requests_mock.get(url, text="cocorico")
    res = nexity.download_soup_from_url(url)
    assert isinstance(res, BeautifulSoup)
    assert res.text == "cocorico"


def test_download_nexity_biens_from_url(nexity_list_html, requests_mock):
    url = "http://test.com"
    requests_mock.get(url, content=nexity_list_html)
    res = nexity.download_nexity_biens_from_url(url)
    assert isinstance(res, list)
    assert len(res) == 41


def test_download_and_save_from_url(nexity_list_html, requests_mock, tmp_path: Path):
    url = "http://test.com"
    requests_mock.get(url, content=nexity_list_html)
    file_path = tmp_path / "export.parquet"
    nexity.download_and_save_nexity_biens_from_url(url, file_path)
    assert file_path.exists()


def test_today(freezer):
    now = datetime(2000, 1, 1)
    freezer.move_to(now)

    res = nexity.generate_today()
    assert res == now.date()


def test_generate_signal_html_filename():
    dt = date(2000, 1, 1)
    res = nexity.generate_signal_html_filename_for_dt(dt)
    assert res.endswith(".html")


def test_save_bytes_to_and_read(tmp_path):
    path = tmp_path / "file.txt"
    content = b"toto"
    nexity.save_bytes_to(content, path)
    res = nexity.read_bytes_from(path)
    assert res == content


def test_download_signal_content(requests_mock):
    url = "http://test.com"
    requests_mock.get(url, content=b"coco")
    nexity.SIGNAL_URL = url
    res = nexity.download_signal_content()
    res == b"coco"


def test_download_and_save_signal_html(requests_mock, tmp_path: Path):
    url = "http://test.com"
    requests_mock.get(url, content=b"coco")
    nexity.SIGNAL_URL = url
    folder_path = tmp_path
    nexity.download_and_save_signal_html(folder_path)
    n_files = len(list(tmp_path.iterdir()))
    assert n_files == 1


def test_load_biens_from_file(nexity_file_path: Path):
    dt = datetime(3000, 1, 2)
    res = nexity.load_biens_from_file_loaded_at(nexity_file_path, dt)
    assert isinstance(res, list)
    assert len(res) == 41
    assert isinstance(res[0], nexity.NexityBien)
    assert res[0].date_loaded == dt


def test_load_biens_from_scrapped_file(tmp_path: Path, nexity_list_html):
    file = tmp_path / "signal_2019_12_31.html"
    file.write_bytes(nexity_list_html)

    res = nexity.load_biens_from_scrapped_file(file)

    dt = datetime(2019, 12, 31)
    assert isinstance(res, list)
    assert len(res) == 41
    assert isinstance(res[0], nexity.NexityBien)
    assert res[0].date_loaded == dt


def test_load_biens_from_scrapping_folder(tmp_path: Path, nexity_list_html):
    scrapping_folder = tmp_path
    file = scrapping_folder / "signal_2019_12_31.html"
    file.write_bytes(nexity_list_html)
    file = scrapping_folder / "signal_2021_12_31.html"
    file.write_bytes(nexity_list_html)

    res = nexity.load_biens_from_scrapping_folder(scrapping_folder)

    assert isinstance(res, list)
    assert len(res) == 41 * 2
    assert {res[0].date_loaded, res[-1].date_loaded} == {
        datetime(2019, 12, 31),
        datetime(2021, 12, 31),
    }


def test_extract_files_of_ext_from_folder(tmp_path: Path):
    print(tmp_path)
    file_1 = tmp_path / "file_1.html"
    file_1.touch()
    file_other = tmp_path / "file_2.ext"
    file_other.touch()
    file_2 = tmp_path / "file_2.html"
    file_2.touch()
    res = nexity.extract_files_of_ext_from_folder(tmp_path, "html")
    assert set(res) == {file_1, file_2}


def test_export_biens_from_scrapping_folder_to_parquet(
    tmp_path: Path, nexity_list_html
):
    scrapping_folder = tmp_path
    file = scrapping_folder / "signal_2019_12_31.html"
    file.write_bytes(nexity_list_html)
    file = scrapping_folder / "signal_2021_12_31.html"
    file.write_bytes(nexity_list_html)

    parquet_file = tmp_path / "export.parquet"

    nexity.export_biens_from_scrapping_folder_to_parquet(scrapping_folder, parquet_file)

    df_exports = pd.read_parquet(parquet_file)
    assert df_exports.shape == (41 * 2, 13)


def test_export_biens_from_scrapping_folder_to_std_parquet(tmp_path: Path):
    scrapping_folder = tmp_path
    path_expected = scrapping_folder / "export.parquet"
    assert not path_expected.is_file()
    nexity.export_biens_from_scrapping_folder_to_std_parquet(scrapping_folder)
    assert path_expected.is_file()


def test_extract_date_from_signal_stem():
    dt = date(2015, 1, 12)
    stem = nexity.generate_signal_stem_for_date(dt)
    dt_extracted = nexity.extract_date_from_signal_stem(stem)
    assert dt == dt_extracted


def test_extract_date_from_signal_html_file():
    signal_html_file = "signal_2022_09_12.html"
    expected = date(2022, 9, 12)
    dt_extracted = nexity.extract_date_from_signal_html_file(signal_html_file)
    assert expected == dt_extracted
