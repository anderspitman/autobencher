import json
import os

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, url

from autobencher.util import Authorization
from autobencher.factory import BenchmarkerFactory


def process_post(factory, request):
    event = json.loads(request.body.decode('utf-8'))

    parser = factory.makeEventParser(event)
    event_data = parser.getEventData()

    if event_data.valid:
        comment_username = os.environ['REPORT_USERNAME']
        comment_password = os.environ['REPORT_PASSWORD']

        report_auth = Authorization(comment_username, comment_password)
        reporter = factory.makeReporter(event_data.reporter_data,
                                        event_data.report_uri,
                                        report_auth)
        runner = factory.makeRunner(os.getcwd(),
                                    event_data.repository_uri,
                                    event_data.repository_base,
                                    event_data.branch,
                                    event_data.branch_owner, reporter)
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
    url(r"/runs/(.*)", StaticFileHandler, { 'path': 'runs' }),
    ])

if __name__ == "__main__":
    app.listen(int(os.environ['PORT']))
    IOLoop.current().start()
