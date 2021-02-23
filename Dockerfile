FROM ubuntu:20.04 AS builder

RUN apt-get update\
 && apt-get install -y python3-pip \
                       python3-dev \
                       python3-venv \
                       python3-wheel

RUN pip3 install poetry

COPY . /tmp/src/
RUN cd /tmp/src && poetry build -f wheel

RUN mkdir /app && cd /app && python3 -m venv venv
RUN /app/venv/bin/pip install /tmp/src/dist/*.whl



FROM ubuntu:20.04
LABEL maintainer="Nicolas Gilles <nicolas.gilles@gmail.com>"

RUN apt-get update && apt-get install -y python3
COPY --from=builder /app /app

ENTRYPOINT ["/app/venv/bin/sitemon"]