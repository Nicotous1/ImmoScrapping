from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import execjs
import re
from .. import nexity

JSON = Dict[str, Any]

def load_data_from_html_path(file:Path)->List[JSON]:
    html_code = file.read_text()

    # Extraire le code JavaScript entre les balises <script>

    js_code = "\n".join(re.findall(r"<script>(.*?)</script>", html_code, re.DOTALL))
    js_code = "window = {};" + js_code

    # Exécuter et récupérer la variable
    context = execjs.compile(js_code)
    data = context.eval(
        "window.__NUXT__.state.productDetails.lots"
    )  # Évaluer la variable 'data'
    return data

def extract_float_or_none(x:Optional[Any])->Optional[float]:
    return x if x is None else float(x)

def extract_bool_from_yes_no(x:Optional[Any])->bool:
    if x == "OUI":
        return True
    elif x == "NON":
        return False
    raise ValueError(f"value yes or no '{x}' could not be converted to boolean")

def extract_orientation_from_item(item:JSON)->"nexity.Orientation":
    south, east, west, north = extract_bool_from_yes_no(item["orientation_sud"]), extract_bool_from_yes_no(item["orientation_est"]), extract_bool_from_yes_no(item["orientation_ouest"]), extract_bool_from_yes_no(item["orientation_nord"])
    if north and west:
        return nexity.Orientation.NORTH_WEST
    elif south and east:
        return nexity.Orientation.SOUTH_EAST
    elif south and west:
        return nexity.Orientation.SOUTH_WEST
    elif north and east:
        return nexity.Orientation.NORTH_EAST
    raise ValueError(f"Orientation is not managed yet south, east, west, north = ({south, east, west, north})")

def extract_type_from_item(x:Optional[Any])->"nexity.BienType":
    if x == "Appartement":
        return nexity.BienType.APPARTEMENT
    if x == "Studio":
        return nexity.BienType.STUDIO
    raise ValueError(f"could not extract bientype from '{x}'")

def convert_data_item_to_nexity_bien(item:JSON, date_loaded:datetime)->"nexity.NexityBien":
    return nexity.NexityBien(
        id=str(item["nb_lot"]),
        type=extract_type_from_item(item["type_bien"]),
        price=float(item["prixNeufTva"]),
        price_low_tva=extract_float_or_none(item["prixFullTax"]),
        date_livraison=item["date_dispo"],
        size=int(item["surface"]),
        floor=int(item["etage"]),
        orientation=extract_orientation_from_item(item),
        has_balcony=bool(item["balcon"]),
        has_terasse=extract_bool_from_yes_no(item["terrasse"]),
        n_parking=int(item["parking"]),
        n_pieces=str(item["nb_piece"]),
        date_loaded=date_loaded,
    )

def load_nexity_bien_from_html_path(file:Path, date_loaded:datetime)->List["nexity.NexityBien"]:
    datas = load_data_from_html_path(file)
    return [convert_data_item_to_nexity_bien(item, date_loaded) for item in datas]