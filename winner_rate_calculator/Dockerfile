FROM ubuntu:18.04
RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika
COPY winner_rate_calculator /
COPY common /common
CMD ["python", "./main.py"]