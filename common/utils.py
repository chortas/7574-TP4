import pika
import time
import logging
import struct

ACK_SCHEME = struct.Struct('?')

def create_connection_and_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    return connection, connection.channel()

def create_queue(channel, queue_name):
    channel.queue_declare(queue=queue_name, durable=True)

def create_exchange(channel, exchange_name, exchange_type):
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)

def send_message(channel, body, queue_name='', exchange_name=''):
    channel.basic_publish(exchange=exchange_name, routing_key=queue_name, body=body,
    properties=pika.BasicProperties(
        delivery_mode=2,  # make message persistent
    ))

def create_and_bind_queue(channel, exchange_name, routing_keys=[], queue_name=''):
    if queue_name:
        channel.queue_declare(queue=queue_name, durable=True)
    else:
        result = channel.queue_declare(queue='', durable=True)
        queue_name = result.method.queue

    if len(routing_keys) == 0:
        channel.queue_bind(exchange=exchange_name, queue=queue_name)

    for routing_key in routing_keys:
        channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
    return queue_name

def consume(channel, queue_name, callback, auto_ack=True):
    logging.info('Waiting for messages. To exit press CTRL+C')
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=auto_ack)
    channel.start_consuming()