"""
api.py
All API route endpoints

:copyright: (C) 2014 by github.com/alfg.
:license:   MIT, see README for more details.
"""

from datetime import timedelta

from flask import request, jsonify, json, Response
from flask.ext.classy import FlaskView, route

from app import app, meta, auth, auth_enabled
from app.utils import obj_to_dict, get_server_conf, get_server_port, get_all_users_count, conditional, support_jsonp
from app.cvp import cvp_chan_to_dict

import Murmur


class ServersView(FlaskView):
    """
    Primary interface for creating, reading and writing to mumble servers.
    """

    @conditional(auth.login_required, auth_enabled)
    def index(self):
        """
        Lists all servers
        """

        servers = []
        for s in meta.getAllServers():
            servers.append({
                'id': s.id(),
                'name': get_server_conf(meta, s, 'registername'),
                'address': '%s:%s' % (
                    get_server_conf(meta, s, 'host'),
                    get_server_port(meta, s),
                ),
                'host': get_server_conf(meta, s, 'host'),
                'port': get_server_port(meta, s),
                'running': s.isRunning(),
                'users': (s.isRunning() and len(s.getUsers())) or 0,
                'maxusers': get_server_conf(meta, s, 'users') or 0,
                'channels': (s.isRunning() and len(s.getChannels())) or 0,
                'uptime_seconds': s.getUptime() if s.isRunning() else 0,
                'uptime': str(
                    timedelta(seconds=s.getUptime()) if s.isRunning() else ''
                ),
                'log_length': s.getLogLen()
            })

        # Workaround response due to jsonify() not allowing top-level json response
        # https://github.com/mitsuhiko/flask/issues/170
        return Response(json.dumps(servers, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    def get(self, id):
        """
        Lists server details
        """

        id = long(id)
        s = meta.getServer(id)

        # Return 404 if not found
        if s is None:
            return jsonify(message="Not Found"), 404

        tree = obj_to_dict(s.getTree()) if s.isRunning() else None

        json_data = {
            'id': s.id(),
            'name': get_server_conf(meta, s, 'registername'),
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
            'running': s.isRunning(),
            'uptime': s.getUptime() if s.isRunning() else 0,
            'humanize_uptime': str(
                timedelta(seconds=s.getUptime()) if s.isRunning() else ''
            ),
            'parent_channel': tree['c'] if s.isRunning() else None,
            'sub_channels': tree['children'] if s.isRunning() else None,
            'users': tree['users'] if s.isRunning() else None,
            'registered_users': s.getRegisteredUsers('') if s.isRunning() else None,
            'log_length': s.getLogLen(),
            'bans': s.getBans() if s.isRunning() else 0
        }

        return jsonify(json_data)

    @conditional(auth.login_required, auth_enabled)
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

        return self.get(server.id())

    @conditional(auth.login_required, auth_enabled)
    def delete(self, id):
        """
        Shuts down and deletes a server
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        # Stop server first if it is running
        if server.isRunning():
            server.stop()

        # Delete server instance
        server.delete()
        return jsonify(message="Server deleted")

    @conditional(auth.login_required, auth_enabled)
    @route('delete', methods=['DELETE'])
    def delete_multiple(self):
        """
        Delete multiple servers.
        """

        id = request.args.get('id')
        if not id:
            return jsonify(message="No servers to delete.")

        ids = map(int, id.split(","))

        # Delete each server.
        for i in ids:
            server = meta.getServer(i)

            if not server:
                continue

            if server.isRunning():
                server.stop()

            server.delete()

        return jsonify(message="Deleting servers.", ids=ids)

    ##
    # Nested routes and actions
    ##
    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/start', methods=['POST'])
    def start(self, id):
        """ Starts server
        """

        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        # Message if server is already running
        if server.isRunning():
            return jsonify(message="Server already running.")

        # Start server instance
        server.start()
        return jsonify(message="Server started.")

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/stop', methods=['POST'])
    def stop(self, id):
        """ Stops server
        """

        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        # Stop server first if it is running
        if not server.isRunning():
            return jsonify(message="Server already stopped.")

        # Stop server instance
        server.stop()
        return jsonify(message="Server stopped.")

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/logs', methods=['GET'])
    def logs(self, id):
        """ Gets all server logs by server ID
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        logs = []

        for l in server.getLog(0, -1):
            logs.append({
                "message": l.txt,
                "timestamp": l.timestamp,
            })
        return Response(json.dumps(logs, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/user/<user>', methods=['DELETE'])
    def user_del_user(self, id, user):
        """ Deletes user
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="No Server Found for ID " + str(id)), 500

        olduser = server.getRegistration(int(user))

        if olduser is None:
            return jsonify(message="No User Found for ID " + str(user)), 500

        server.unregisterUser(int(user))

        json_data = {
            "user_id": user,
            "deleted": 'Success'
        }
        return Response(json.dumps(json_data, sort_keys=True, indent=4), mimetype='application/json')


    @conditional(auth.login_required, auth_enabled)
    @route('<id>/user', methods=['POST'])
    def user_new_user(self, id):
        """ Creates user
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        username = request.form.get('username')
        password = request.form.get('password')

        new_user = {
            Murmur.UserInfo.UserName: username,
            Murmur.UserInfo.UserPassword: password
        }

        added = server.registerUser(new_user)

        data = obj_to_dict(server.getRegistration(added))

        json_data = {
            "user_id": added,
            "username": data['UserName'],
            "last_active": data['UserLastActive']
        }
        return Response(json.dumps(json_data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/user/<user>', methods=['GET'])
    def register_user(self, id, user):
        """ Gets registered user by ID
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getRegistration(int(user)))

        json_data = {
            "user_id": user,
            "username": data['UserName'],
            "last_active": data['UserLastActive']
        }
        return Response(json.dumps(json_data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/channels', methods=['GET'])
    def channels(self, id):
        """ Gets all channels in server
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getChannels())

        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/channels/<channel_id>', methods=['GET'])
    def channel(self, id, channel_id):
        """ Gets a specific channel from a server
        """

        server = meta.getServer(int(id))

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getChannelState(int(channel_id)))

        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/bans', methods=['GET'])
    def bans(self, id):
        """ Gets all banned IPs in server
        """

        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getBans())
        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/conf', methods=['GET'])
    def conf(self, id):
        """ Gets all configuration in server
        """

        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getAllConf())
        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/conf', methods=['POST'])
    def set_conf(self, id):
        """ Change a configuration variable on a server.
        """

        key = request.form.get('key')
        value = request.form.get('value')

        if key and value:
            server = meta.getServer(id)

            # Return 404 if not found
            if server is None:
                return jsonify(message="Not Found"), 404

            server.setConf(key, value)
            return jsonify(message="Configuration updated.")
        else:
            server = meta.getServer(id)

            # Return 404 if not found
            if server is None:
                return jsonify(message="Not Found"), 404

            count = 0
            for key, val in request.form.items():
                count += 1
                server.setConf(key, val)

            if count > 0:
                return jsonify(message="Configuration updated: %d values." % count)
            else:
                return jsonify(message="Configuration key and value required.")

    @conditional(auth.login_required, auth_enabled)
    @route('<id>/channels/<channel_id>/acl', methods=['GET'])
    def channel_acl(self, id, channel_id):
        """ Gets all channel ACLs in server
        """

        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        data = obj_to_dict(server.getACL(channel_id))
        return Response(json.dumps(data, sort_keys=True, indent=4), mimetype='application/json')

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/sendmessage', methods=['POST'])
    def send_message(self, id):
        """ Sends a message to all channels in a server
        """

        message = request.form.get('message')

        if message:
            server = meta.getServer(id)

            # Return 404 if not found
            if server is None:
                return jsonify(message="Not Found"), 404

            server.sendMessageChannel(0, True, message)
            return jsonify(message="Message sent.")
        else:
            return jsonify(message="Message required.")

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/setsuperuserpw', methods=['POST'])
    def set_superuser_pw(self, id):
        """ Sets SuperUser password for server id
        """

        password = request.form.get('password')

        if password:
            server = meta.getServer(id)

            # Return 404 if not found
            if server is None:
                return jsonify(message="Not Found"), 404

            server.setSuperuserPassword(password)
            return jsonify(message="Superuser password set.")
        else:
            return jsonify(message="Password required.")

    @conditional(auth.login_required, auth_enabled)
    @route('<int:id>/kickuser', methods=['POST'])
    def kick_user(self, id):
        """ Kicks user from server.
        """

        user_session = int(request.form.get("usersession"))  # Session ID of user
        reason = request.form.get("reason", "Reason not defined.")  # Reason messaged for being kicked.

        if user_session:
            server = meta.getServer(id)

            # Return 404 if not found
            if server is None:
                return jsonify(message="Not Found"), 404

            try:
                server.kickUser(user_session, reason)
                return jsonify(message="User kicked from server.")

            except Murmur.InvalidSessionException:
                return jsonify(message="Not a valid session ID.")

        else:
            return jsonify(message="User session required.")


class StatsView(FlaskView):
    """
    View for gathering stats on murmur statistics.
    """

    @conditional(auth.login_required, auth_enabled)
    def index(self):
        """
        Lists all stats
        """

        stats = {
            'all_servers': len(meta.getAllServers()),
            'booted_servers': len(meta.getBootedServers()),
            'users_online': get_all_users_count(meta),
            'murmur_version': meta.getVersion()[3],
            'murmur-rest_version': '0.1',
            'uptime': meta.getUptime()
        }

        # Workaround response due to jsonify() not allowing top-level json response
        # https://github.com/mitsuhiko/flask/issues/170
        return Response(json.dumps(stats, sort_keys=True, indent=4), mimetype='application/json')

class CVPView(FlaskView):
    """
    View for display CVP on servers where it is enabled.
    """

    @support_jsonp
    @route('<int:id>', methods=['GET'])
    def cvp(self, id):
        server = meta.getServer(id)

        # Return 404 if not found
        if server is None:
            return jsonify(message="Not Found"), 404

        allowed = bool(get_server_conf(meta, server, 'x_cvp'))
        if not allowed:
            return jsonify(message="CVP Disabled"), 403

        # Fetch tree from server
        tree = server.getTree()

        # Get server properties relevant to CVP
        rname = get_server_conf(meta, server, 'registername')
        rhost = get_server_conf(meta, server, 'registerhostname')
        port = get_server_port(meta, server)

        # Build the CVP object
        cvp = {
            "root": cvp_chan_to_dict(tree),
            "name": rname if rname != '' else 'Root',
            "x_uptime": server.getUptime(),
            "id": server.id()
        }

        if rhost != '':
            cvp['x_connecturl'] = "mumble://%s:%d/?version=1.2.0" % (rhost, port)

        return Response(json.dumps(cvp, sort_keys=True, indent=4), mimetype='application/json')

# Register views
ServersView.register(app)
StatsView.register(app)
CVPView.register(app)

if __name__ == '__main__':
    app.run(debug=True)

