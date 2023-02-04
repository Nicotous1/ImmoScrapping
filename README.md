[![Test, Build and Deploy to Lambda](https://github.com/Nicotous1/ImmoScrapping/actions/workflows/test_build_and_deploy.yml/badge.svg)](https://github.com/Nicotous1/ImmoScrapping/actions/workflows/test_build_and_deploy.yml)

# Env

conda activate ImmoScrap

# Scrapping Nexity current page

python downloads/run.py

# Exporting all scrapping html to one parquet

python downloads/export.py

# Analyse the exported parquet

devs/analyse.py in notebook mode
