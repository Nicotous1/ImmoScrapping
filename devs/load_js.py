# %%
from pathlib import Path

import execjs

# Page HTML avec JavaScript
html_code = Path("../downloads/debug/signal_2024_12_20.html").read_text()

# Extraire le code JavaScript entre les balises <script>
import re

js_code = "\n".join(re.findall(r"<script>(.*?)</script>", html_code, re.DOTALL))
js_code = "window = {};" + js_code

# Exécuter et récupérer la variable
context = execjs.compile(js_code)
data = context.eval(
    "window.__NUXT__.state.productDetails.lots"
)  # Évaluer la variable 'data'
print("Contenu de data :", data)
