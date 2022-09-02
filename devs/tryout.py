# %%
import requests

url = "https://www.nexity.fr/neuf/0099__98124"
res = requests.get(url)

# %%
f = open("nexity_list.html", "wb")
f.write(res.content)
f.close()

#%%
# open and read the file after the appending:
f = open("nexity_list.html", "rb")
content = f.read()
f.close()


# %%
class_identifier = ".product--lots-details .content"
from bs4 import BeautifulSoup

soup = BeautifulSoup(content, "html.parser")
