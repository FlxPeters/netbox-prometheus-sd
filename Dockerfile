###############################################
# Base Image
###############################################
FROM python:3.8-alpine as python-base
# https://www.mktr.ai/the-data-scientists-quick-guide-to-dockerfiles-with-examples/

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_VERSION=1.1.4 \
  POETRY_HOME="/opt/poetry" \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_NO_INTERACTION=1 \
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

###############################################
# Builder Image
###############################################
FROM python-base as builder-base
RUN apk add --no-cache curl

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --no-dev

###############################################
# Production Image
###############################################
FROM python-base as production

COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY netbox-prometheus-sd.py /app/netbox-prometheus-sd.py
COPY netbox_sd /app/netbox_sd
RUN chmod +x /app/netbox-prometheus-sd.py

# Create data volume directory
RUN mkdir -p /data/netbox&& \
  chown -R nobody:nogroup /data/netbox

# Add curl and upgrade all os packages
RUN apk --update --no-cache upgrade && apk --no-cache add curl
HEALTHCHECK --interval=30s --timeout=1s --start-period=5s \
  CMD curl -f http://localhost:8000/ || exit 1

VOLUME "/data/netbox"
USER nobody
WORKDIR /data/netbox

ENV NETBOX_SD_FILE_PATH /data/netbox/netbox.json
ENV NETBOX_SD_METRICS_PORT 8000

EXPOSE 8000

CMD [ "/app/netbox-prometheus-sd.py"]