FROM alpine:latest

RUN apk update \
    && apk add python3 build-base python3-dev linux-headers \
    && python3 -m ensurepip \
    && python3 -m pip install --upgrade pip

RUN pip3 install speedtest-cli 'influxdb-client[ciso]' ischedule psutil requests

RUN mkdir /ukcoviddata-loader /data
WORKDIR /ukcoviddata-loader

COPY loader.py /ukcoviddata-loader

ENTRYPOINT ["python3", "/ukcoviddata-loader/loader.py"]