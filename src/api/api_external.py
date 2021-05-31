import json

import requests
from decouple import config
from flask import jsonify, redirect, request

from src.api.helper import serialize
from src.cache.cache import cache
from src.messages.client_message import ClientMessage


def external_routes(api):
    ip = config("CONTAINER_IP")
    port = config("CONTAINER_PORT")

    @api.route('/', methods=['GET'])
    def root():
        return redirect('/status', code=302)

    @api.route('/status', methods=['GET'])
    def status():
        return jsonify(dict(status='OK', message={
            'internal_ip': ip,
            'note': 'This is only an External API to get data from redis database',
            'port': port,
            'endpoints': [
                {'method': 'GET', 'locator': '/status', 'description': 'shows the status of the external api'},
                {'method': 'GET', 'locator': '/nodes', 'description': 'shows all nodes and leader node'},
                {'method': 'GET', 'locator': '/nodes?ip=<NodeIP>',
                 'description': 'get detail about node using Node\'s internal IP'},
                {'method': 'GET', 'locator': '/elections', 'description': 'shows all elections for each term'},
                {'method': 'GET', 'locator': '/elections?term=<TermNo>', 'description': 'get election for a term'},
                {'method': 'GET', 'locator': '/leaders', 'description': 'shows all leaders for each term'},
                {'method': 'GET', 'locator': '/leaders?term=<TermNo>', 'description': 'get leader for a term'},
                {'method': 'GET', 'locator': '/logs', 'description': 'get logs for all nodes'},
                {'method': 'GET', 'locator': '/logs?ip=<NodeIP>', 'description': 'get logs for node with IP'},
                {'method': 'GET', 'locator': '/nodes/move?x=<N>&y=<N>',
                 'description': 'move leader node and other nodes <N> units. <N> can be +ve or -ve'},
                {'method': 'GET', 'locator': '/nodes/position',
                 'description': 'get current positions of all nodes in raft'},
                {'method': 'GET', 'locator': '/nodes/full', 'description': 'get full details of all nodes in raft'},
            ],
        })), 200

    @api.route('/nodes', methods=['GET'])
    def nodes():
        node_ip = request.args.get('ip', None)
        all_nodes = cache.get('nodes')
        all_nodes = json.loads(all_nodes) if all_nodes else None

        if all_nodes:
            if node_ip:
                filtered = list(filter(lambda node: node['_name'] == f'{node_ip.strip()}:{port}', all_nodes))
                if len(filtered) > 0:
                    resp = requests.get(f'http://{node_ip}:{port}', timeout=10)
                    data = resp.json()
                    return jsonify(dict(status='OK', data=data['message'],
                                        message=f"Successfully fetched node with IP {node_ip}")), 200
                else:
                    return jsonify(dict(status='404', data=None, message=f"No node with IP {node_ip} in raft")), 404
            else:
                return jsonify(dict(status='OK', data=all_nodes, message="Successfully fetched nodes")), 200
        else:
            return jsonify(dict(status='404', data=None, message="No node in raft so far")), 404

    @api.route('/elections', methods=['GET'])
    def elections():
        term = request.args.get('term', None)
        election = cache.get('election')
        election = json.loads(election) if election else None

        if election:
            if term:
                term_election = election.get(term, None)
                if term_election:
                    return jsonify(dict(status='OK', data=term_election,
                                        message=f"Successfully fetched election for term (Term {term})")), 200
                else:
                    return jsonify(dict(status='404', data=None, message=f"No election for term (Term {term})")), 404
            else:
                return jsonify(dict(status='OK', data=election, message="Successfully fetched elections")), 200
        else:
            return jsonify(dict(status='404', data=None, message="No election so far")), 200

    @api.route('/leaders', methods=['GET'])
    def leaders():
        term = request.args.get('term', None)
        leader = cache.get('leader')
        leader = json.loads(leader) if leader else None

        if leader:
            if term:
                term_leader = leader.get(term, None)
                if term_leader:
                    return jsonify(dict(status='OK', data=term_leader,
                                        message=f"Successfully fetched leader for term (Term {term})")), 200
                else:
                    return jsonify(dict(status='404', data=None, message=f"No leader for term (Term {term})")), 404
            else:
                return jsonify(dict(status='OK', data=leader, message="Successfully fetched leaders")), 200
        else:
            return jsonify(dict(status='404', data=None, message="No leader so far")), 200

    @api.route('/logs', methods=['GET'])
    def logs():
        node_ip = request.args.get('ip', None)
        all_nodes = cache.get('nodes')
        all_nodes = json.loads(all_nodes) if all_nodes else None

        if all_nodes:
            if node_ip:
                filtered = list(filter(lambda node: node['_name'] == f'{node_ip.strip()}:{port}', all_nodes))
                if len(filtered) > 0:
                    resp = requests.get(f'http://{node_ip}:{port}/logs', timeout=10)
                    data = resp.json()
                    return jsonify(dict(status='OK', data=data['message'],
                                        message=f"Successfully fetched node logs with IP {node_ip}")), 200
                else:
                    return jsonify(dict(status='404', data=None, message=f"No node with IP {node_ip} in raft")), 404
            else:
                result = []
                for n in all_nodes:
                    resp = requests.get(f"http://{n['_name']}/logs")
                    data = resp.json()
                    result.append(data)
                return jsonify(dict(status='OK', data=result, message="Successfully fetched nodes logs")), 200
        else:
            return jsonify(dict(status='404', data=None, message="No node in raft so far")), 404

    @api.route('/nodes/move', methods=['GET'])
    def move_nodes():
        x = int(request.args.get('x', '0'))
        y = int(request.args.get('y', '0'))
        leaders = cache.get('leader')
        leaders = json.loads(leaders) if leaders else None

        if leaders:
            term = max(leaders, key=int)
            leader = leaders.get(term)
            node_addr = leader['_name']

            message = ClientMessage(
                'CLIENT_IP',
                node_addr,
                leader['term'],
                {
                    "move": [x, y],
                }
            )

            resp = requests.post(f'http://{node_addr}/message', json=serialize(message), timeout=60)
            data = resp.json()

            if data and hasattr(data, '__getitem__'):
                return jsonify(dict(status='OK', data=data,
                                    message=f"Nodes moved successfully. Controlled by leader {node_addr}")), 200
            else:
                return jsonify(dict(status='OK', data=data,
                                    message=f"Failed to move leader node: {node_addr}\nCould "
                                            f"be that the leader is unavailable due to an ongoing election")), 200
        else:
            return jsonify(dict(status='404', data=None, message="No leader appointed yet in raft")), 404

    @api.route('/nodes/position', methods=['GET'])
    def nodes_position():
        all_nodes = cache.get('nodes')
        all_nodes = json.loads(all_nodes) if all_nodes else None
        response = []

        if all_nodes:
            for node in all_nodes:
                try:
                    resp = requests.get(f"http://{node['_name']}/status", timeout=60)
                    data = resp.json()
                    if data:
                        message = data.get('message', {}).get('node', {})
                        response.append({'node': message.get('_name'), 'position': message.get('_position')})
                except:
                    print('Unfortunate')
            return jsonify(dict(status='OK', data=response,
                            message='Successfully fetched node positions')), 200
        else:
            return jsonify(dict(status='404', data=None, message="No node in raft so far")), 404

    @api.route('/nodes/full', methods=['GET'])
    def nodes_full():
        all_nodes = cache.get('nodes')
        all_nodes = json.loads(all_nodes) if all_nodes else None
        response = []

        if all_nodes:
            for node in all_nodes:
                try:
                    resp = requests.get(f"http://{node['_name']}/status", timeout=60)
                    data = resp.json()
                    if data:
                        response.append(data)
                except:
                    print('Unfortunate')
            return jsonify(dict(status='OK', data=response,
                            message='Successfully fetched node positions')), 200
        else:
            return jsonify(dict(status='404', data=None, message="No node in raft so far")), 404

