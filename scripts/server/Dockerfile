FROM ubuntu:20.04

# Timezone Configuration
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ADD rmq-srv.py /scripts

# RUN python3 /scripts/server/rmq-srv.py