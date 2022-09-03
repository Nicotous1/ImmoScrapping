#!/usr/bin/env python

"""Tests for `immo_scrap` package."""

from datetime import datetime
from pathlib import Path
import pytest
from bs4 import Tag

from immo_scrap import nexity, factories
import pandas as pd


@pytest.fixture
def nexity_table_tag(nexity_list_soup) -> Tag:
    return nexity.extract_tables_from_soup(nexity_list_soup)[0]


@pytest.fixture
def nexity_table_v2_tag(nexity_list_soup) -> Tag:
    return nexity.extract_tables_from_soup(nexity_list_soup)[1]


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
                    "Type": "Appartement",
                    "Prix TVA 20%": "303 700 €",
                    "Livraison": "3ème trimestre 2025",
                    "Surface": "46 m²",
                    "Étage": "Étage 17",
                    "Orientation": "Nord-Ouest",
                    "Les +": "",
                },
                nexity.NexityLine(
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
        ],
    )
    def test_create_from_dict(self, datas, expected):
        res = nexity.NexityLine.create_from_dict(datas)
        assert res == expected


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
    return nexity.NexityBien.create_from_nexity_table(nexity_table)


class Test_NexityBien:
    def test_create_from_nexity_table(self, nexity_table, freezer):
        now = datetime(2000, 1, 1)
        freezer.move_to(now)
        res = nexity.NexityBien.create_from_nexity_table(nexity_table)
        assert isinstance(res, list)
        assert len(res) == 8
        res_1 = res[1]
        assert isinstance(res_1, nexity.NexityBien)
        assert res_1.n_pieces == nexity_table.n_pieces
        assert res_1.date_loaded == now


def test_extract_nexity_tables_from_soup(nexity_list_soup):
    res = nexity.extract_nexity_tables_from_soup(nexity_list_soup)
    assert isinstance(res, list)
    assert len(res) == 3
    res_1 = res[1]
    assert isinstance(res_1, nexity.NexityTable)


def test_convert_nexity_biens_to_dataframe(nexity_biens):
    res = nexity.convert_nexity_biens_to_dataframe(nexity_biens)
    assert isinstance(res, pd.DataFrame)
    assert res.shape == (8, 12)
    assert res.iloc[0]["type"] == "Appartement"
    assert res.iloc[0]["orientation"] == "Nord-Ouest"


def test_extract_nexity_biens_from_soup(nexity_list_soup):
    res = nexity.extract_nexity_biens_from_soup(nexity_list_soup)
    assert isinstance(res, list)
    assert len(res) == 41


def test_save_nexity_biens(tmp_path: Path):
    file_path = tmp_path / "biens.json"
    biens = factories.NexityBienFactory.create_batch(5)
    nexity.save_nexity_biens_to_parquet(biens, file_path)
    assert file_path.exists() is True
    parquet = pd.read_parquet(file_path)
    assert parquet.shape == (5, 12)
