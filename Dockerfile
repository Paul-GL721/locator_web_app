# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

# Maintainer information
LABEL maintainer="Paul GL <lwangapaul23@gmail.com>"

# Create necessary directories, aligning with Kubernetes mounts
RUN mkdir -p /code/workdir
RUN mkdir -p /code/staticfiles
RUN mkdir -p /code/config

# Set working directory 
WORKDIR /code/workdir

RUN apt-get update && apt-get install -y \
    binutils libproj-dev gdal-bin netcat-traditional tzdata

# Install pipenv and dependencies
RUN pip install pipenv
COPY Pipfile Pipfile.lock /code/workdir/
RUN pipenv install --system --deploy


# Copy project files into workdir 
ADD ./ /code/workdir/

# Copy entrypoint script and make it executable
COPY --chmod=755 entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
