#! /usr/bin/env python3

from flask import Flask, request
import pika
import logging
import os
from pathlib import Path
import json
from pymongo import MongoClient
from time import time
logging.basicConfig(level=logging.INFO)

class DBApp:
    def __init__(self, appPort, mdbAddr):
        self.host = "0.0.0.0"
        self.port = appPort
        self.mdbAddr = mdbAddr
        mongo = MongoClient(self.mdbAddr)
        self.db = mongo['collabse-db']
        self.app = Flask(__name__)
        self._configure_requests()

    def run(self, debug=False):
        self.app.run(debug=debug, host=self.host, port=self.port)

    def _configure_requests(self):
        self.app.add_url_rule('/', view_func=self.index, methods=['GET'])
        self.app.add_url_rule('/api/tasks/append', view_func=self.add_task, methods=['PUT'])
        self.app.add_url_rule('/api/tasks/lookup', view_func=self.get_task, methods=['GET'])
        self.app.add_url_rule('/api/tasks/update', view_func=self.update_task, methods=['POST'])
        # self.app.add_url_rule('/add-job/<cmd>', view_func=self.add, methods=['GET', 'POST'])
        # self.app.add_url_rule("/client.js", view_func=self.javascript, methods=['GET'])

    def update_task(self):
        key = request.args.get('key')
        task_upd = {}
        task_upd['status'] = request.args.get('status').lower()
        out_file = request.data.decode("utf-8")
        if out_file != "":
            task_upd['out_file'] = out_file
        self.db['tasks'].update_one({'key': key}, {'$set': task_upd})
        return "OK"
        
    def add_task(self):
        task = {}
        task['name'] = request.args['name']
        task['key'] = str(int(time() * 10e6))
        task['status'] = "pending"
        task['out_file'] = ""
        self.db['tasks'].insert_one(task)
        return {'name': task['name'], 'key': task['key'], 'status': task['status']}
    
    def get_task(self):
        key = request.args.get('key')
        task = self.db['tasks'].find_one({'key': key})
        if task is None:
            return {'status': 'not found', 'out_file': '', 'key': key, 'name': ''}
        return {'name': task['name'], 'key': task['key'], 'status': task['status'], 'out_file': task['out_file']}

    def index(self):
        return "OK"

if __name__ == '__main__':
    app = DBApp(appPort=8070, mdbAddr="mongodb://admin:admin@127.0.0.1:27017/collabse-db")
    app.run()