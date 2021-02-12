FROM debian:buster-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

WORKDIR /opt/murmur-rest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    libevent-dev \
    software-properties-common

# Install ZeroC Ice.
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv B6391CB2CFBA643D && \
    apt-add-repository "deb http://zeroc.com/download/ice/3.7/debian10 stable main" && \
    apt-get update && apt-get install -y python3-zeroc-ice zeroc-ice-compilers

# Create virtual env and setup Python app.
ADD requirements.txt /opt/murmur-rest/requirements.txt
RUN python3 -m venv --system-site-packages venv && \
    ./venv/bin/pip3 install -r requirements.txt

# Cleanup.
RUN apt-get autoremove -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# Add config files.
ADD ./etc/murmur.ini /etc/murmur.ini

# Add app.
ADD . /opt/murmur-rest

EXPOSE 8080

CMD ["/opt/murmur-rest/venv/bin/gunicorn", "-b", "0.0.0.0:8080", "-w", "4", "-k", "gevent", "wsgi:app"]