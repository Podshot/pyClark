import time
import tornado.ioloop
import tornado.web
import tornado.auth

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from github import Github

import os
import uuid
import atexit
import re

from tornado.httpclient import AsyncHTTPClient

LISTEN_PORT = int(os.environ.get('PORT', 80))
ALLOWED_USERS = os.environ.get('USERS', '').split(',')
PUBLIC_VIEW = False

db_path = os.environ.get('DATABASE_URL', 'sqlite:////' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.db').replace('\\', '/').replace('C:/', ''))
engine = create_engine(db_path)
Base = declarative_base(bind=engine)

class ErrorReport(Base):
    __tablename__ = 'reports'
    report_id = Column(String, primary_key=True)
    report_time = Column(Integer)
    os = Column(String)
    stacktrace = Column(String)
    
    def __init__(self, *args, **kwargs):
        super(ErrorReport, self).__init__(*args, **kwargs)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
atexit.register(session.close)

SETTINGS = {
    "template_path": os.path.join(os.path.dirname(__file__), 'templates'),
    "static_path": os.path.join(os.path.dirname(__file__), 'static'),
    "cookie_secret": os.environ.get('COOKIE_SECRET', '<enter in your own secret cookie>'),
    "login_url": '/login',
    'debug': True
}

class BaseHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        username = self.get_secure_cookie('user')
        if not username:
            return None
        username = username.decode('utf-8')
        if username in ALLOWED_USERS:
            return self.get_secure_cookie('user')
        else:
            self.clear_cookie('user')
            return None

class IndexPageHandler(tornado.web.RequestHandler):

    def collect_reports(self):
        reports = session.query(ErrorReport).all()
        regex = re.compile(r'/(\w)+\.py\"')
        for report in reports:
            error = report.stacktrace
            parts = error.strip().split('\n')
            match = regex.search(parts[-3])
            if not match:
                continue
            report['filename'] = match.group(0)[1:-1]
            report['exception'] = parts[-1].split(':')[0]
            yield report

    def get(self):
        #self.write('Test page')
        #self.flush()
        self.render('index.html', reports=self.collect_reports(), fields=('report_time', 'report_id', 'os', 'filename', 'exception'))

class LoginHandler(tornado.web.RequestHandler):

    def get(self):
        self.render('login.html')
        g = Github(self.get_argument('token', default=''))

    def post(self, *args, **kwargs):
        username = self.get_argument('username')
        token = self.get_argument('token')
        g = Github(token)
        user = g.get_user(username)

        if user.login in ALLOWED_USERS:
            self.set_secure_cookie('user', user.login)
        self.redirect('/')


class ReportErrorPage(tornado.web.RequestHandler):

    def post(self, *args, **kwargs):
        os = self.get_argument('os')
        stacktrace = self.get_argument('stack-trace')
        local_vars = self.get_argument('locals')
        global_vars = self.get_argument('globals')
        report_uuid = str(uuid.uuid4())

        stacktrace = re.sub(r'([A-Z]{1}\:/[Uu]sers/)([^/]*)', '<user>', stacktrace)
        stacktrace = re.sub(r'/home/\w+/', '<user>', stacktrace)
        #self.write(str(uuid.uuid4()))

        report = ErrorReport(
            report_id=report_uuid,
            report_time=time.time(),
            os=os,
            stacktrace=stacktrace
        )
        session.add(report)
        session.commit()

        self.set_header('Content-Type', 'application/json')
        self.write({'id': report_uuid})
        self.flush()


class ReportDetailPage(BaseHandler):

    def get(self, *args, **kwargs):
        if not self.get_current_user() and not PUBLIC_VIEW:
            self.redirect('/login')
            return
        report_id = args[0]
        report = session.query(ErrorReport).filter(ErrorReport.report_id == report_id).first()
        self.render('error_details.html', report=report, section=self.get_query_argument('section', 'summary'), can_delete=(self.get_current_user() is not None))

class DeleteReportHandler(BaseHandler):

    def get(self):
        if not self.get_current_user():
            self.redirect('/')
            return
        report_id = self.get_query_argument('id', default='')
        report = session.query(ErrorReport).filter(ErrorReport.report_id == report_id).first()
        if report:
            session.query(ErrorReport).filter(ErrorReport.report_id == report_id).delete()
            session.commit()
        self.redirect('/')


if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/', IndexPageHandler),
        (r'/login', LoginHandler),
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': SETTINGS['static_path']}),
        (r'/report-error', ReportErrorPage),
        (r'/error/(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})', ReportDetailPage),
        (r'/delete-report', DeleteReportHandler)
    ], **SETTINGS)

    tornado.httpclient.AsyncHTTPClient.configure('tornado.curl_httpclient.CurlAsyncHTTPClient')

    app.listen(LISTEN_PORT)
    tornado.ioloop.IOLoop.current().start()
