FROM python:3.7-alpine
RUN apk update
RUN apk add docker
RUN pip3 install pika
COPY monitor /
COPY common /common
CMD ["python", "./main.py"]
