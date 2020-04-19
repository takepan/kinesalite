FROM node:8.16.0-stretch-slim

RUN apt update && apt install build-essential python-minimal -y
RUN npm install --unsafe-perm -g kinesalite
RUN apt install vim -y
RUN apt install python3-pip -y
RUN apt-get clean

ADD . /usr/local/src

WORKDIR /usr/local/src

RUN pip3 install -r requirements.txt

CMD ["kinesalite", "--port", "4567", "--createStreamMs", "5"]
