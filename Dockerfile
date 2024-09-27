FROM python:3.12.4-slim

RUN pip install poetry
RUN apt-get update && \
    apt-get -y install gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /equiteez
COPY poetry.lock pyproject.toml /equiteez/
COPY dipdup.yml /equiteez/
COPY dipdup.contracts.yml /equiteez/
COPY dipdup.prod.yml /equiteez/

RUN poetry config virtualenvs.create false && poetry install --no-dev

ADD equiteez /equiteez/equiteez/

ENTRYPOINT ["poetry", "run", "dipdup", "-c", "dipdup.prod.yml", "-c", "dipdup.contracts.yml", "-c", "dipdup.yml", "run"]

EXPOSE 9090/tcp
