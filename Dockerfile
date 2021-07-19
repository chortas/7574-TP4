FROM ubuntu:18.04
RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika
ENV MATCH_QUEUE=match_queue
ENV MATCH_FILE=3_4_matches.csv
ENV PLAYER_QUEUE=player_queue
ENV PLAYER_FILE=3_4_players.csv
ENV BATCH_TO_SEND=100000
ENV N_LINES=5000
ENV API_IP=interface
ENV API_PORT=3002
COPY client.py /
COPY main.py /
COPY 3_4_players.csv /
COPY 3_4_matches.csv /
COPY common /common
CMD ["python3", "./main.py"]
