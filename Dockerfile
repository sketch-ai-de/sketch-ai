FROM ubuntu:22.04

RUN apt-get update -y
RUN apt-get install -y gnupg2 wget
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt jammy-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    libpq-dev \
    locales \
    python3 \
    python3-pip \
    postgresql \
    postgresql-16-pgvector \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

RUN localedef -f UTF-8 -i en_US en_US.UTF-8

WORKDIR /sketch-ai
ADD ./requirements.txt /sketch-ai/requirements.txt
RUN pip install -r requirements.txt

COPY ./.env /sketch-ai/
COPY ./*.py /sketch-ai/
COPY ./docs /sketch-ai/docs
COPY ./entrypoint.sh /sketch-ai/

# TODO(qu): in mid-term sketch-ai should allow adding new data to database without rebuilding the docker image
COPY ./chroma_db /sketch-ai/chroma_db

ENTRYPOINT ["/sketch-ai/entrypoint.sh"]
