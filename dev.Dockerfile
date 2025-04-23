# syntax=docker/dockerfile:1
#FROM python:3.9-bullseye
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/dev-code:/dev-code/apmsystem:/usr/local/lib/python3.10/site-packages"
ENV PIPENV_VENV_IN_PROJECT=1

# Maintainer information
LABEL maintainer="Paul GL <lwangapaul23@gmail.com>"

# Install dependencies and Python 3 with pip
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    binutils libproj-dev gdal-bin netcat-traditional

# Ensure pip3 is installed correctly
RUN apt-get install -y python3-distutils

# Copy wait-for script and make it executable
COPY wait-for /wait-for 
RUN chmod +x /wait-for

RUN mkdir /dev-code
# Create necessary directories
RUN mkdir -p /dev-code/staticfiles

# Set working directory
WORKDIR /dev-code

# Install pipenv and dependencies
RUN pip3 install pipenv
COPY Pipfile Pipfile.lock /dev-code/
RUN pipenv install --system --deploy


# Copy project files
ADD ./ /dev-code/
