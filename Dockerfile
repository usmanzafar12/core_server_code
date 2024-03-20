FROM nickgryg/alpine-pandas:3.7
WORKDIR /code
ENV INFLUX_TOKEN=""
ENV INFLUXDB_CONNECTION="infludb:8086"
ENV PORT=8001
RUN apk add --no-cache --update \
    python3 python3-dev gcc \
    gfortran musl-dev g++ \
    libffi-dev openssl-dev \
    libxml2 libxml2-dev \
    libxslt libxslt-dev \
    libjpeg-turbo-dev zlib-dev \
    gcc linux-headers
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
#COPY . .
CMD ["python", "simple-server.py"]