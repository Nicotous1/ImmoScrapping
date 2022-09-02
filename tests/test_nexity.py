#!/usr/bin/env python

"""Tests for `immo_scrap` package."""

import pytest
from bs4 import Tag

from immo_scrap import nexity
import pandas as pd


@pytest.fixture
def nexity_table_tag(nexity_list_soup) -> Tag:
    return nexity.extract_tables_from_soup(nexity_list_soup)[0]


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


class Test_NexityTable:
    def test_create_from_table_tag(self, nexity_table_tag):
        res = nexity.NexityTable.create_from_table_tag(nexity_table_tag)
        assert isinstance(res, nexity.NexityTable)
        df = res.df
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (8, 7)
        assert res.title == "2 pièces"
        assert res.n_theoric == 8


def test_extract_nexity_tables_from_soup(nexity_list_soup):
    res = nexity.extract_nexity_tables_from_soup(nexity_list_soup)
    assert isinstance(res, list)
    assert len(res) == 3
    res_1 = res[1]
    assert isinstance(res_1, nexity.NexityTable)
