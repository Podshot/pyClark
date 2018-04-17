import sys
import json
import threading
import traceback
import types
import logging
import platform
import atexit

import requests

from . import utils

logger = logging.getLogger(__name__)

def stop_all_threads():
    for thread in Clark._threads:
        thread.stop()
        thread.join()

atexit.register(stop_all_threads)

class SendReportThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(SendReportThread, self).__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self):
        self._stop_evt.set()

    def stopped(self):
        return self._stop_evt.is_set()

class Clark(object):

    _already_injected = False
    _object_serializers = {}
    _threads = []

    @classmethod
    def add_serializer(cls, clazz):
        cls._object_serializers[clazz.serialize_type] = clazz()

    def __init__(self, hostname, inject=False, **kwargs):
        self._hostname = hostname
        if inject and not self._already_injected:
            module = sys.modules[__name__.split('.')[0]]
            setattr(module, 'global_clark', self)
            self.__class__._already_injected = True
        elif inject:
            logger.warning('A Clark object has already injected into the module')
        self._post_endpoint = kwargs.get('post_endpoint', 'report-error')
        self._show_report_id = kwargs.get('show_report_id', True)
        self._allow_logging = kwargs.get('allow_logging', True)
        self._timeout = kwargs.get('timeout', 8)

    def report(self, error=None, *args, **kwargs):
        if not error:
            error = ''.join(traceback.format_exception(*sys.exc_info()))

        def can_serialize(value):
            if type(value) in self._object_serializers:
                value = self._object_serializers[type(value)].serialize(value)
            try:
                json.dumps({'var': value})
                return True
            except:
                return False

        def try_dump(obj):
            if isinstance(obj, types.ModuleType):
                return {'type': 'module', 'name': obj.__name__}
            t = str(type(obj))
            data = {
                'type': t,
                'data': 'Unknown'
            }
            try:
                data['data'] = {}
                for k, v in obj.__dict__.items():
                    if not can_serialize(v):
                        continue
                    if not (hasattr(obj, 'dont_serialize') or type(v) in self._object_serializers):
                        data['data'][k] = v
                    elif not hasattr(obj, 'dont_serialize') and type(v) in self._object_serializers:
                        data['data'][k] = self._object_serializers[type(v)].serialize(v)
            except Exception as e:
                    pass
            return data

        lcls = kwargs.get('locals', {})
        glbls = kwargs.get('globals', {})
        report = {
            'locals': {name: try_dump(data) for name, data in lcls.items()},
            'globals': {name: try_dump(data) for name, data in glbls.items()},
            'stack-trace': error,
            'os': platform.platform()
        }
        report = utils.anonymize(json.dumps(report))

        proc = SendReportThread(target=self._send, args=(report,))
        proc.daemon = True
        self._threads.append(proc)
        proc.start()

        proc.join(self._timeout)

        if proc.is_alive():
            proc.stop()
            proc.join()

        self._threads.remove(proc)
        #self._send(report)

    def _send(self, report_dict):
        try:
            reply = requests.post('{}/{}'.format(self._hostname, self._post_endpoint), data={'info': report_dict}, timeout=self._timeout)
        except requests.exceptions.Timeout:
            logger.critical('Could not send error report')
            logger.warning('Request timed out. Timeout = {}'.format(self._timeout))
            return
        except Exception as e:
            logger.error(e)
            logger.critical('Could not send error report')
            return
        if self._allow_logging:
            if reply.status_code == 200:
                if self._show_report_id:
                    logger.info('Successfully sent error report. Report ID: {}'.format(reply.json()['id']))
                else:
                    logger.info('Successfully sent error report')
            else:
                logger.warning("Report was not sent successfully, code: {} reason: {}".format(reply.status_code, reply.reason))
