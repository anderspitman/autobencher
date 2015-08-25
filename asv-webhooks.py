import json
import os

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, url

from benchmark_runner import BenchmarkRunner

class WebhooksHandler(RequestHandler):
    
    def post(self):
        event_data = json.loads(self.request.body.decode('utf-8'))

        # hand off to a new process. This is necessary since we need to change
        # the working directory for ASV to work, but we also need to be able
        # to handle concurrent ASV runs. Only handle pull requests that are
        # being opened or synchronized for now
        if ('pull_request' in event_data and
            event_data['action'] in ('opened', 'synchronize')):
            runner = BenchmarkRunner.makeBenchmarkRunner(os.getcwd(),
                                                         event_data)
            runner.run()

app = Application([
    url(r"/webhooks", WebhooksHandler),
    url(r"/runs/(.*)", StaticFileHandler, { 'path': 'runs' }),
    ])

if __name__ == "__main__":
    app.listen(int(os.environ['PORT']))
    IOLoop.current().start()
