FROM ubuntu:20.04

# Timezone Configuration
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && apt install -y    apt-utils \
                                    lsb-release \
                                    mesa-utils \
                                    gnupg2 \
                                    net-tools \
                                    build-essential \
                                    wget \
                                    unzip \
                                    curl \
                                    git \
                                    nano \
                                    iputils-ping \
                                    cmake \
                                    psmisc \
                                    python3-pip \
                                    python3-dev

RUN pip3 install flask pika

ENTRYPOINT python3 /scripts/rmq-worker.py
# RUN python3 /scripts/worker/rmq-worker.py