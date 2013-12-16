def obj_to_dict(obj):
    rv = {'_type': str(type(obj))}

    if type(obj) in (bool, int, float, str, unicode):
        return obj

    if type(obj) in (list, tuple):
        return [obj_to_dict(item) for item in obj]

    if type(obj) == dict:
        return dict((str(k), obj_to_dict(v)) for k, v in obj.iteritems())

    return obj_to_dict(obj.__dict__)


def get_server_conf(meta, server, key):
    val = server.getConf(key)
    if '' == val:
        val = meta.getDefaultConf().get(key, '')
    return val


def get_server_port(meta, server, val=None):
    val = server.getConf('port') if val == None else val

    if '' == val:
        val = meta.getDefaultConf().get('port', 0)
        val = int(val) + server.id() - 1

    return int(val)