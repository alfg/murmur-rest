import os
from datetime import timedelta, datetime
from flask import Flask
from flask import request, jsonify, json, Response
from flask.ext.classy import FlaskView, route

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
                'channels': (s.isRunning() and len(s.getChannels())) or 0,
                'uptime': s.getUptime() if s.isRunning() else 0,
                'fuzzy_uptime': str(
                    timedelta(seconds=s.getUptime()) if s.isRunning() else ''
                ),
                'log_length': s.getLogLen()
            })

        # Workaround response due to jsonify() not allowing top-level json response
        # https://github.com/mitsuhiko/flask/issues/170
        return Response(json.dumps(servers, sort_keys=True, indent=4), mimetype='application/json')

    def get(self, id):
        """
        Lists server details
        """

        s = meta.getServer(id)
        tree = obj_to_dict(s.getTree())

        json_data = {
            'id': s.id(),
            'name': get_server_conf(meta, s, 'registerName'),
            'host': get_server_conf(meta, s, 'host'),
            'port': get_server_port(meta, s),
            'address': '%s:%s' % (
                get_server_conf(meta, s, 'host'),
                get_server_port(meta, s),
            ),
            'password': get_server_conf(meta, s, 'password'),
            'welcometext': get_server_conf(meta, s, 'welcometext'),
            'user_count': (s.isRunning() and len(s.getUsers())) or 0,
            'maxusers': get_server_conf(meta, s, 'users') or 0,
            'uptime': s.getUptime() if s.isRunning() else 0,
            'fuzzy_uptime': str(
                timedelta(seconds=s.getUptime()) if s.isRunning() else ''
            ),
            'parent_channel': tree['c'],
            'sub_channels': tree['children'],
            'users': obj_to_dict(s.getUsers()),
            'registered_users': s.getRegisteredUsers(''),
            'log_length': s.getLogLen(),
            'bans': s.getBans()
        }

        return jsonify(json_data)

    def post(self):
        """
        Creates a server, starts server, and returns id
        """

        # Basic Configuration
        password = request.form.get('password')
        port = request.form.get('port')  # Defaults to inifile+server_id-1
        timeout = request.form.get('timeout')
        bandwidth = request.form.get('bandwidth')
        users = request.form.get('users')
        welcometext = request.form.get('welcometext')

        # Data for registration in the public server list
        registername = request.form.get('registername')
        registerpassword = request.form.get('registerpassword')
        registerhostname = request.form.get('registerhostname')
        registerurl = request.form.get('registerurl')

        # Create server
        server = meta.newServer()

        # Set conf if provided
        server.setConf('password', password) if password else None
        server.setConf('port', port) if port else None
        server.setConf('timeout', timeout) if timeout else None
        server.setConf('bandwidth', bandwidth) if bandwidth else None
        server.setConf('users', users) if users else None
        server.setConf('welcometext', welcometext) if welcometext else None
        server.setConf('registername', registername) if registername else None

        # Start server
        server.start()

        # Format to JSON
        json_data = {
            'id': server.id()
        }

        return jsonify(json_data)

    def delete(self, id):
        """
        Shuts down and deletes a server
        """

        server = meta.getServer(id)
        server.stop()
        server.delete()
        return jsonify(message="Server deleted")

    # Nested routes and actions
    @route('<id>/logs', methods=['GET'])
    def logs(self, id):
        """ Gets all server logs by server ID
        """

        server = meta.getServer(id)
        logs = []

        for l in server.getLog(0, -1):
            logs.append({
                "message": l.txt,
                "timestamp": l.timestamp,
            })
        return Response(json.dumps(logs, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/register/<user>', methods=['GET'])
    def register_user(self, id, user):
        """ Gets registered user by ID
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getRegistration(user))

        json_data = {
            "user_id": user,
            "username": data['UserName'],
            "last_active": data['UserLastActive']
        }
        return Response(json.dumps(json_data, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/channels', methods=['GET'])
    def channels(self, id):
        """ Gets all channels in server
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getChannels())

        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/channels/<channel_id>', methods=['GET'])
    def channel(self, id, channel_id):
        """ Gets all channels in server
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getChannelState(channel_id))

        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/bans', methods=['GET'])
    def bans(self, id):
        """ Gets all banned IPs in server
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getBans())
        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/conf', methods=['GET'])
    def conf(self, id):
        """ Gets all configuration in server
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getAllConf())
        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @route('<id>/channels/<channel_id>/acl', methods=['GET'])
    def channel_acl(self, id, channel_id):
        """ Gets all channel ACLs in server
        """

        server = meta.getServer(id)
        data = obj_to_dict(server.getACL(channel_id))

        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')


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

