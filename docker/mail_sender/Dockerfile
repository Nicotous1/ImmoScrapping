FROM python:3.9


COPY ./immo_scrap .
COPY ./setup.py .

RUN pip install .

COPY ./downloads/run.py .

CMD python run.py