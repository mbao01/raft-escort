import json
from decouple import config
from flask import request, jsonify, redirect

from src.node.node import Node
from src.api.helper import uptime, serialize, Map


def internal_routes(api):
    ip = config("CONTAINER_IP")
    port = config("CONTAINER_PORT")

    node_name = f'{ip}:{port}'
    node = Node(name=node_name)  # any new node is first a follower by default

    @api.route('/', methods=['GET'])
    def root():
        return redirect('/status', code=302)

    @api.route('/status', methods=['GET'])
    def status():
        return jsonify(dict(status='OK', message={
            'age': {
                'created': node._creationTime,
                'uptime': uptime(node._creationTime)
            },
            'internal_ip': ip,
            'name': node_name,
            'port': port,
            'node': serialize(node)
        })), 200

    @api.route('/logs', methods=['GET'])
    def logs():
        return jsonify(dict(status='OK', message={
            'logs': node._log,
            'name': node_name,
            'port': port,
            'node': serialize(node)
        })), 200

    @api.route('/message', methods=['POST'])
    def message():
        message = json.loads(request.data)  # { term, payload }
        message = Map(message)
        response = node._state.on_receive_message(message=message)

        return jsonify(serialize(response))  # send response back to leader
