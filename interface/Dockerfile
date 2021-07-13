FROM ubuntu:18.04
RUN apt update && apt install python3 python3-pip -y
RUN pip3 install pika
COPY interface /
COPY common /common
CMD ["python", "./main.py"]