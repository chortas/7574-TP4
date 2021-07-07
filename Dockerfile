FROM ubuntu:18.04
RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika
ENV MATCH_QUEUE=match_queue
ENV MATCH_FILE=matches.csv
ENV PLAYER_QUEUE=player_queue
ENV PLAYER_FILE=match_players.csv
ENV BATCH_TO_SEND=100000
COPY client.py /
COPY main.py /
COPY match_players.csv /
COPY matches.csv /
COPY common /common
CMD ["python3", "./main.py"]
