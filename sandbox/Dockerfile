FROM python:3.12-slim

RUN pip install --no-cache-dir matplotlib==3.9.2

RUN useradd --create-home --shell /bin/bash sandbox

WORKDIR /code
RUN mkdir -p /tmp/output && chown -R sandbox:sandbox /code /tmp

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER sandbox

ENTRYPOINT ["/entrypoint.sh"]
