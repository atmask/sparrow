FROM python:3.12-slim-bullseye

LABEL org.opencontainers.image.source https://github.com/atmask/sparrow

## Install dependencies (curl)
RUN apt-get -y update; apt-get -y install curl git

# Create a non-root-user group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

## No shell entrypoint for root
RUN chsh -s /usr/sbin/nologin root

## Mount and install the wheel
RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

## Install gunicorn
RUN pip install --upgrade gunicorn

## Set the user to non-root
USER appuser

WORKDIR /app

## Create a bin dir for app installations and add to path
RUN mkdir -p /app/bin
ENV PATH="/app/bin:${PATH}"


## Preload gunicorn on single proc to do do bin install for release manager
CMD ["gunicorn", "sparrow.server:app", "-w", "5", "-b", "5000", "--preload"] 