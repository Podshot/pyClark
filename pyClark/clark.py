import json
import types
import requests

class WatchDog(object):

    _ready = False
    _hostname = None

    @classmethod
    def _suitup(cls, hostname, *args, **kwargs):
        if cls._ready:
            return
        cls._ready = True
        cls._hostname = hostname


    @classmethod
    def report(cls, error, *args, **kwargs):

        if not cls._ready:
            cls._suitup()

        def try_dump(obj):
            if isinstance(obj, types.ModuleType):
                return obj.__name__
            t = str(type(obj))
            try:
                return "type={} : data={}".format(t, json.dumps(obj))
            except Exception as e:
                try:
                    return "type={} : data={}".format(t, json.dumps(obj.__dict__))
                except:
                    return "type={} : data=Unknown".format(t)

        lcls = kwargs.get('locals', {})
        glbls = kwargs.get('globals', {})
        report = {
            'locals': {name: try_dump(data) for name, data in lcls.items()},
            'globals': {name: try_dump(data) for name, data in glbls.items()},
            'stack-trace': error
        }
        print(report)
