FROM python:3.12.4-slim

RUN pip install poetry==1.8.4
RUN apt-get update && \
    apt-get -y install gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /indexer
COPY poetry.lock pyproject.toml /indexer/
COPY dipdup.yml /indexer/
COPY dipdup.contracts.yml /indexer/
COPY dipdup.prod.yml /indexer/

RUN poetry config virtualenvs.create false && poetry install --only main

ADD equiteez /indexer/equiteez/

ENTRYPOINT ["poetry", "run", "dipdup", "-c", "dipdup.prod.yml", "-c", "dipdup.contracts.yml", "-c", "dipdup.yml", "run"]

EXPOSE 9090/tcp
