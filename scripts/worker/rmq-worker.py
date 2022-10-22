#! /usr/bin/env python3

import pika
import time
import logging
import os
logging.basicConfig(level=logging.INFO)

class RMQHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue='task_queue', durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue='task_queue', on_message_callback=self.callback)
    
    def start(self):
        logging.info(" [*] Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()

    def callback(self, ch, method, properties, body):
        logging.info(" [x] Received %r" % body)
        cmd = body.decode()

        if cmd == 'hey':
            print("hey there")
        elif cmd == 'hello':
            print("well hello there")
        else:
            print("sorry i did not understand ", body)

        ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    node = RMQHandler("0.0.0.0", 5672)
    sleepTime = 10
    logging.info("Sleeping for %d seconds" % sleepTime)
    # time.sleep(sleepTime)
    node.start()
