import os
from datetime import timedelta, datetime
from flask import Flask
from flask import jsonify, json
from flask.ext.classy import FlaskView

import config
from utils import obj_to_dict, get_server_conf, get_server_port

import Ice

app = Flask(__name__)

Ice.loadSlice('', ['-I' + Ice.getSliceDir(), os.path.join(app.root_path, config.SLICE_FILE)])
import Murmur
ice = Ice.initialize()
proxy = ice.stringToProxy('Meta:tcp -h localhost -p 6502'.encode('ascii'))
meta = Murmur.MetaPrx.checkedCast(proxy)


class ServersView(FlaskView):
    route_prefix = '/api/v1/'

    def index(self):
        """
        Lists all servers
        """
        servers = []
        for s in meta.getAllServers():
            servers.append({
                'id': s.id(),
                'name': get_server_conf(meta, s, 'registerName'),
                'address': '%s:%s' % (
                    get_server_conf(meta, s, 'host'),
                    get_server_port(meta, s),
                ),
                'running': s.isRunning(),
                'users': (s.isRunning() and len(s.getUsers())) or 0,
                'maxusers': get_server_conf(meta, s, 'users') or 0,
                'uptime': s.getUptime() if s.isRunning() else 0,
                'fuzzy_uptime': str(
                    timedelta(seconds=s.getUptime()) if s.isRunning() else ''
                ),
            })

        return jsonify(servers=servers)

    def get(self, id):
        """
        Lists server details
        """

        s = meta.getServer(id)
        tree = obj_to_dict(s.getTree())

        server = {
            'config': {
                'port': get_server_port(meta, s)
            },
            'id': s.id(),
            'name': get_server_conf(meta, s, 'registerName'),
            'users': (s.isRunning() and len(s.getUsers())) or 0,
            'maxusers': get_server_conf(meta, s, 'users') or 0,
            'uptime': s.getUptime() if s.isRunning() else 0,
            'fuzzy_uptime': str(
                timedelta(seconds=s.getUptime()) if s.isRunning() else ''
            ),
            'tree': tree
        }

        return jsonify(server=server)

    def post(self):
        """
        Creates a server, starts server, and returns id
        """

        server = meta.newServer()
        server.start()

        json_data = {
            'id': server.id()
        }

        return jsonify(server=json_data)

    def delete(self, id):
        """
        Shuts down and deletes a server
        """

        server = meta.getServer(id)
        server.stop()
        server.delete()
        return jsonify(message="Server deleted")


class LogsView(FlaskView):
    route_prefix = '/api/v1/'

    def index(self):
        return jsonify(message="Please provide a server ID")

    def get(self, id):
        server = meta.getServer(id)
        logs = []

        for l in server.getLog(0, -1):
            logs.append({
                "text": l.txt,
                "timestamp": l.timestamp,
            })

        return jsonify(log=logs)



ServersView.register(app)
LogsView.register(app)

if __name__ == '__main__':
    app.run(debug=True)

