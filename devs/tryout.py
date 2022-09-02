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
print(f.read())
f.close()
