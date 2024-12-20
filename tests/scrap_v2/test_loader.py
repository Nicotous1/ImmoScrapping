from datetime import datetime
from pathlib import Path
from immo_scrap.scrap_v2 import loader
from immo_scrap.nexity import NexityBien, NexityLine

test_folder = Path(__file__).parent
test_file = test_folder / "signal_2024_12_20.html"
test_old_file = test_folder / "../nexity_list.html"

def test_loader_html_has_4_lots():
    res = loader.load_data_from_html_path(test_file)
    assert isinstance(res, list)
    assert len(res) == 4

def test_loader_html_get_nexity_biens():
    date_loaded = datetime.now()
    res = loader.load_nexity_bien_from_html_path(test_file, date_loaded)
    assert isinstance(res, list)
    assert len(res) == 4
    item = res[0]
    assert isinstance(item, NexityBien)

def test_loader_html_get_nexity_biens_on_old_file():
    date_loaded = datetime.now()
    res = loader.load_nexity_bien_from_html_path(test_old_file, date_loaded)
    assert isinstance(res, list)
    assert len(res) == 41
    item = res[0]
    assert isinstance(item, NexityBien)
