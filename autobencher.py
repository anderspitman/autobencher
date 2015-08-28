import json
import os

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, url

from autobencher.util import Authorization
from autobencher.factory import BenchmarkerFactory


class EventHandler(RequestHandler):

    def initialize(self):
        self._factory = BenchmarkerFactory.makeFactory()
    
    def post(self):
        event = json.loads(self.request.body.decode('utf-8'))

        # log webhooks request
        with open('webhooks_request.json', 'w') as webhooks_request_fp:
            json.dump(event, webhooks_request_fp, indent=4,
                      sort_keys=True)

        parser = self._factory.makeEventParser(event)
        event_data = parser.getEventData()

        if event_data.valid:
            comment_username = os.environ['REPORT_USERNAME']
            comment_password = os.environ['REPORT_PASSWORD']

            report_auth = Authorization(comment_username, comment_password)
            reporter = self._factory.makeReporter(event_data.result_uri,
                                                  event_data.report_uri,
                                                  report_auth)
            runner = self._factory.makeRunner(os.getcwd(),
                                              event_data.repository_uri,
                                              event_data.repository_base,
                                              event_data.branch,
                                              event_data.branch_owner, reporter)
            runner.run()


app = Application([
    url(r"/webhooks", EventHandler),
    url(r"/runs/(.*)", StaticFileHandler, { 'path': 'runs' }),
    ])

if __name__ == "__main__":
    app.listen(int(os.environ['PORT']))
    IOLoop.current().start()
