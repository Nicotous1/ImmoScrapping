from pathlib import Path
import pytest
from bs4 import BeautifulSoup


test_folder = Path(__file__).parent 

@pytest.fixture
def nexity_list_html()->bytes:
    f = open(test_folder / "nexity_list.html", "rb")
    content = f.read()
    f.close()
    return content

@pytest.fixture
def nexity_list_soup(nexity_list_html:bytes)->BeautifulSoup:
    soup = BeautifulSoup(nexity_list_html, 'html.parser')
    return soup
    