import json
import os

from tornado.web import RequestHandler, StaticFileHandler, Application, url

from autobencher.util import Authorization
from autobencher.factory import BenchmarkerFactory


def process_post(factory, request):
    event = json.loads(request.body.decode('utf-8'))

    parser = factory.makeEventParser(event)
    event_data = parser.get_event_data()

    if event_data.valid:
        comment_username = os.environ['REPORT_USERNAME']
        comment_password = os.environ['REPORT_PASSWORD']
        hostname = os.environ['HOSTNAME']
        port = os.environ['PORT']
        result_address = hostname + ':' + port

        report_auth = Authorization(comment_username, comment_password)
        reporter = factory.makeReporter(event_data.reporter_data, report_auth,
                                        result_address)
        runner = factory.makeRunner(os.getcwd(), event_data.runner_data,
                                    reporter)
        run_location = runner.get_run_location()
        log_event(event, run_location)

        runner.run()


class EventHandler(RequestHandler):

    def initialize(self):
        self._factory = BenchmarkerFactory.makeFactory()

    def post(self):
        process_post(self._factory, self.request)


def log_event(event, directory):
    log_path = os.path.join(directory, 'request.json')
    with open(log_path, 'w') as request_fp:
        json.dump(event, request_fp, indent=4,
                  sort_keys=True)

app = Application([
    url(r"/webhooks", EventHandler),
    url(r"/runs/(.*)", StaticFileHandler, {'path': 'runs'}),
    ])
