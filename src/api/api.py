import redis
from decouple import config
from flask import Flask
from src.api.api_external import external_routes
from src.api.api_internal import internal_routes

api = Flask(__name__)

api.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

port = config("CONTAINER_PORT")
server_type = config("API", default='INTERNAL')

print('api_type', server_type)

if server_type == 'EXTERNAL':
    external_routes(api=api)
else:
    internal_routes(api=api)

if __name__ == '__main__':
    api.run(host='0.0.0.0', port=port, debug=True)
