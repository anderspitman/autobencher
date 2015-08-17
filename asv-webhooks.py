from subprocess import check_call
from multiprocessing import Process
import requests
import json
import os
import shutil

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, StaticFileHandler, Application, url

class ASVProcess(Process):
    def __init__(self, directory, event_data):
        super(ASVProcess, self).__init__()
        self._event_data = event_data
        self._dir = directory
        self._pull_request = event_data['pull_request']
        self._base_commit = self._pull_request['base']['sha']
        self._branch_ref = self._pull_request['head']['ref']

        run_dir = os.path.join(self._dir, 'runs')
        self._owner = self._pull_request['head']['repo']['owner']['login']
        self._branch_dir = os.path.join(run_dir, self._owner, self._branch_ref)

        self._server = os.environ['WEBHOOKS_SERVER']
        self._comment_username = os.environ['GITHUB_USER']
        self._comment_password = os.environ['GITHUB_PASS']

    def run(self):
        self._run_asv()
       
    def _run_asv(self):
        self._set_up_environment()
        commit_range = self._base_commit + '..' + self._branch_ref
        asv_command = ['asv', 'run', commit_range]
        check_call(asv_command)
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)
        os.chdir(self._dir)
        self._report_run_finished()

    def _set_up_environment(self):
        clone_url = self._pull_request['head']['repo']['clone_url']

        with open('asv_conf_template.json') as asv_fp:
            asv_config = json.load(asv_fp)
        asv_config['repo'] = clone_url
        asv_config['branches'] = [self._branch_ref]

        if not os.path.exists(self._branch_dir):
            os.makedirs(self._branch_dir)
        benchmark_dir = os.path.join(self._branch_dir, 'benchmarks')
        if os.path.exists(benchmark_dir):
            shutil.rmtree(benchmark_dir)
        shutil.copytree('benchmarks', benchmark_dir)
        os.chdir(self._branch_dir)
        with open('asv.conf.json', 'w') as asv_fp:
            json.dump(asv_config, asv_fp, indent=4, sort_keys=True)

        # log webhooks request
        with open('webhooks_request.json', 'w') as webhooks_request_fp:
            json.dump(self._event_data, webhooks_request_fp, indent=4,
                      sort_keys=True)


    def _report_run_finished(self):
        link_parts = (self._server, 'runs', self._owner, self._branch_ref,
                      'html', 'index.html')
        result_link = os.sep.join(link_parts)
        comments_url = self._pull_request['comments_url']
        comment_body = ("## Automated report from asv run\nBenchmark run "
                        "completed successfully. Results available at\n[%s]"
                        "(%s)") % (result_link, result_link)
        params = {'body': comment_body}
        requests.post(comments_url, data=json.dumps(params),
                      auth=(self._comment_username, self._comment_password))


class WebhooksHandler(RequestHandler):
    
    def post(self):
        event_data = json.loads(self.request.body.decode('utf-8'))

        # hand off to a new process. This is necessary since we need to change
        # the working directory for ASV to work, but we also need to be able
        # to handle concurrent ASV runs. Only handle pull requests that are
        # being opened or synchronized for now
        if ('pull_request' in event_data and
            event_data['action'] in ('opened', 'synchronize')):
            asv_proc = ASVProcess(os.getcwd(), event_data).start()

app = Application([
    url(r"/webhooks", WebhooksHandler),
    url(r"/runs/(.*)", StaticFileHandler, { 'path': 'runs' }),
    ])

if __name__ == "__main__":
    app.listen(5000)
    IOLoop.current().start()
