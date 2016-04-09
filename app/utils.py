"""
utils.py
Utilities used within the application.

:copyright: (C) 2014 by github.com/alfg.
:license:   MIT, see README for more details.
"""

from flask import request, current_app
from functools import wraps

from settings import USERS as users
from app import auth


@auth.get_password
def get_pw(username):
    """
    Required get_password function used for flask-httpauth.
    """
    if username in users:
        return users.get(username)
    return None


class conditional(object):
    """
    A conditional decorator utility.
    """
    def __init__(self, dec, condition):
        self.decorator = dec
        self.condition = condition

    def __call__(self, func):
        if not self.condition:
            # Return the function unchanged, not decorated.
            return func
        return self.decorator(func)


def obj_to_dict(obj):
    """
    Used for converting objects from Murmur.ice into python dict.
    """
    rv = {'_type': str(type(obj))}

    if type(obj) in (bool, int, long, float, str, unicode):
        return obj

    if type(obj) in (list, tuple):
        return [obj_to_dict(item) for item in obj]

    if type(obj) == dict:
        return dict((str(k), obj_to_dict(v)) for k, v in obj.iteritems())

    return obj_to_dict(obj.__dict__)


def get_server_conf(meta, server, key):
    """
    Gets the server configuration for given server/key.
    """
    val = server.getConf(key)
    if '' == val:
        val = meta.getDefaultConf().get(key, '')
    return val


def get_server_port(meta, server, val=None):
    """
    Gets the server port value from configuration.
    """
    val = server.getConf('port') if val == None else val

    if '' == val:
        val = meta.getDefaultConf().get('port', 0)
        val = int(val) + server.id() - 1
    return int(val)


def get_all_users_count(meta):
    """
    Gets the entire list of users online count by iterating through servers.
    """
    user_count = 0
    for s in meta.getAllServers():
        user_count += (s.isRunning() and len(s.getUsers())) or 0
    return user_count

def support_jsonp(f):
    """
    Wraps JSONified output for JSONP
    Copied from https://gist.github.com/aisipos/1094140
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args,**kwargs).data) + ')'
            return current_app.response_class(content, mimetype='application/javascript')
        else:
            return f(*args, **kwargs)
    return decorated_function
