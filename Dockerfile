FROM python:3.9

WORKDIR /app

COPY ./immo_scrap /app/immo_scrap
COPY ./README.rst /app/README.rst
COPY ./HISTORY.rst /app/HISTORY.rst
COPY ./setup.py /app/setup.py
RUN pip install .

COPY ./downloads/ /app/downloads/
COPY ./devs/ /app/devs/

CMD python devs/try_aws.py