
# syntax=docker/dockerfile:1
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PIPENV_VENV_IN_PROJECT=1

# Maintainer information
LABEL maintainer="Paul GL <lwangapaul23@gmail.com>"

# Install dependencies and Python 3 with pip
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    binutils libproj-dev gdal-bin netcat-traditional 
# Install tzdata non-interactively with updated apt-get
RUN apt-get update && DEBIAN_FRONTEND="noninteractive" TZ="Africa/Kampala" apt-get install -y tzdata

# Ensure pip3 is installed correctly
RUN apt-get install -y python3-distutils

# Copy entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create necessary directories, aligning with Kubernetes mounts
RUN mkdir -p /code/workdir
RUN mkdir -p /code/staticfiles
RUN mkdir -p /code/config

# Set working directory 
WORKDIR /code/workdir

# Install pipenv and dependencies
RUN pip3 install pipenv
COPY Pipfile Pipfile.lock /code/workdir/
RUN pipenv install --system --deploy

# Copy project files into workdir 
ADD ./ /code/workdir/

# Set entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
