FROM ubuntu:18.04

WORKDIR /opt/murmur-rest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    software-properties-common

# Install Murmur from PPA.
RUN add-apt-repository ppa:mumble/release && \
    apt-get update && apt-get install -y mumble-server && \
    dpkg-reconfigure mumble-server

# Install ZeroC Ice.
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv B6391CB2CFBA643D && \
    apt-add-repository "deb http://zeroc.com/download/ice/3.7/ubuntu18.04 stable main" && \
    apt-get update && apt-get install -y python3-zeroc-ice zeroc-ice-compilers


# Install supervisor to system.
RUN pip3 install supervisor

# Create virtual env and setup Python app.
ADD requirements.txt /opt/murmur-rest/requirements.txt
RUN python3 -m venv --system-site-packages venv && \
    ./venv/bin/pip3 install -r requirements.txt

# Add config files.
ADD ./etc/mumble-server.ini /etc/mumble-server.ini
ADD ./etc/supervisord.conf /etc/supervisor/supervisord.conf

# Add app.
ADD . /opt/murmur-rest

# Mumble ports. Please note you'll need to expose ports above 50000
# if you wish to support more than 1 virtual instance.
# You can use the range 50000- 65000.
EXPOSE 8080
EXPOSE 50000

CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
