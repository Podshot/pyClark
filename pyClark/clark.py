import sys
import json
import types
import requests
import logging
from . import utils

logger = logging.getLogger(__name__)

class Clark(object):

    _already_injected = False
    _object_serializers = {}

    def __init__(self, hostname, inject=False, **kwargs):
        self._hostname = hostname
        if inject and not self._already_injected:
            module = sys.modules[__name__.split('.')[0]]
            setattr(module, 'global_clark', self)
            self.__class__._already_injected = True
        elif inject:
            logger.warning('A Clark object has already injected into the builtins module')
        self._post_endpoint = kwargs.get('post_endpoint', 'report-error')
        self._show_report_id = kwargs.get('show_report_id', True)
        self._allow_logging = kwargs.get('allow_logging', True)

    def report(self, error, *args, **kwargs):

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
            'stack-trace': error,
            'os': ''
        }
        report = json.loads(utils.anonymize(json.dumps(report)))
        self._send(report)

    def _send(self, report_dict):
        try:
            reply = requests.post('{}/{}'.format(self._hostname, self._post_endpoint), data=report_dict)
        except Exception as e:
            logger.error(e)
            logger.critical('Could not send error report')
            return
        if self._allow_logging:
            if reply.status_code == 200:
                if self._show_report_id:
                    logger.info('Successfully sent error report. Report ID: {}'.format(reply.json()['id']))
                else:
                    logger.info('Sucessfully sent error report')
            else:
                logger.warning("Report was not sent successfully, code: {} reason: {}".format(reply.status_code, reply.reason))
