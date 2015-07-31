from flask import Flask, request, jsonify, send_from_directory
from subprocess import check_call
from multiprocessing import Process

import json
import os
import shutil

class ASVProcess(Process):
    def __init__(self, directory, event_data):
        super(ASVProcess, self).__init__()
        self._dir = directory
        self._server = 'powertrip.mggen.nau.edu:5000'
        self._pull_request = event_data['pull_request']
        self._base_commit = self._pull_request['base']['sha']
        self._branch_ref = self._pull_request['head']['ref']

    def run(self):
       self._run_asv(self._base_commit, self._branch_ref)
       
    def _run_asv(self, start_commit, end_commit):
        self._set_up_environment()
        commit_range = self._base_commit + '..' + self._branch_ref
        asv_command = ['asv', 'run', commit_range]
        check_call(asv_command)
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)
        os.chdir(self._dir)

    def _set_up_environment(self):
        run_dir = os.path.join(self._dir, 'runs')
        clone_url = self._pull_request['base']['repo']['clone_url']
        owner = self._pull_request['head']['repo']['owner']['login']

        with open('asv_conf_template.json') as asv_fp:
            asv_config = json.load(asv_fp)
        asv_config['repo'] = clone_url
        asv_config['branches'] = [self._branch_ref]

        branch_dir = os.path.join(run_dir, owner, self._branch_ref)
        if not os.path.exists(branch_dir):
            os.makedirs(branch_dir)
        benchmark_dir = os.path.join(branch_dir, 'benchmarks')
        if os.path.exists(benchmark_dir):
            shutil.rmtree(benchmark_dir)
        shutil.copytree('benchmarks', benchmark_dir)
        os.chdir(branch_dir)
        with open('asv.conf.json', 'w') as asv_fp:
            json.dump(asv_config, asv_fp, indent=2, sort_keys=True)

    def report_run_finished(self):
        pass


app = Flask(__name__, static_url_path='')

@app.route('/runs/<path:path>')
def results(path):
    return send_from_directory('runs', path)

@app.route("/webhooks", methods=['POST'])
def handle_webhooks():
    # hand off to a new process. This is necessary since we need to change
    # the working directory for ASV to work, but we also need to be able
    # to handle concurrent ASV runs.
    event_data = request.get_json(jsonify(force=True))
    asv_proc = ASVProcess(os.getcwd(), event_data).start()
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
