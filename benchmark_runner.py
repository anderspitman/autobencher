import json
import requests
import os
import shutil

from multiprocessing import Process
from subprocess import check_call
from abc import ABCMeta, abstractmethod


class BenchmarkRunner(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        pass

    @classmethod
    def makeBenchmarkRunner(cls, directory, event_data):
        return ASVBenchmarkRunner(directory, event_data)
        

class ASVBenchmarkRunner(BenchmarkRunner):
    def __init__(self, directory, event_data):
        self._asv_proc = ASVProcess(directory, event_data)

    def run(self):
        self._asv_proc.start()


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
        self._clone_url = self._pull_request['head']['repo']['clone_url']

        hostname= os.environ['HOSTNAME']
        port = os.environ['PORT']
        comment_username = os.environ['REPORT_USERNAME']
        comment_password = os.environ['REPORT_PASSWORD']

        server = hostname + ':' + port
        link_parts = (server, 'runs', self._owner, self._branch_ref,
                      'html', 'index.html')
        result_uri = os.sep.join(link_parts)

        report_auth = Authorization(comment_username, comment_password)
        self._reporter = BenchmarkReporter.makeReporter(
            result_uri, self._pull_request['comments_url'], report_auth)

    def run(self):
        self._run_asv()
       
    def _run_asv(self):
        self._set_up_environment()
        # include 1 previous commit from master so we can see any regressions
        commit_range = self._base_commit + '~1..' + self._branch_ref
        asv_command = ['asv', 'run', '--steps', '10', commit_range]
        check_call(asv_command)
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)
        os.chdir(self._dir)
        self._report_run_finished()
        self._reporter.report_run_finished()

    def _set_up_environment(self):

        if not os.path.exists(self._branch_dir):
            os.makedirs(self._branch_dir)

        self._source_repo = os.path.join(self._branch_dir, 'source_repo')
        branch_name = self._pull_request['head']['ref']
        self._repo = SourceRepository.makeRepository(self._clone_url,
                                                     branch_name,
                                                     self._source_repo)

        source_config = os.path.join(self._source_repo, 'asv.conf.json')
        with open(source_config) as asv_fp:
            asv_config = json.load(asv_fp)
        asv_config['repo'] = self._clone_url
        asv_config['branches'] = [self._branch_ref]

        benchmark_dest = os.path.join(self._branch_dir, 'benchmarks')
        if os.path.exists(benchmark_dest):
            shutil.rmtree(benchmark_dest)
        benchmark_source = os.path.join(self._source_repo, 'benchmarks')
        shutil.copytree(benchmark_source, benchmark_dest)
        os.chdir(self._branch_dir)
        with open('asv.conf.json', 'w') as asv_fp:
            json.dump(asv_config, asv_fp, indent=4, sort_keys=True)

        # log webhooks request
        with open('webhooks_request.json', 'w') as webhooks_request_fp:
            json.dump(self._event_data, webhooks_request_fp, indent=4,
                      sort_keys=True)


class Authorization(object):
    def __init__(self, username, password):
        self._username = username
        self._password = password

    def getUsername(self):
        return self._username

    def getPassword(self):
        return self._password


class SourceRepository(metaclass=ABCMeta):
    @classmethod
    def makeRepository(cls, url, branch, directory):
        return GitRepository(url, branch, directory)

    @abstractmethod
    def __init__(self):
        pass


class GitRepository(SourceRepository):
    def __init__(self, url, branch, directory):
        if os.path.exists(directory):
            cur_dir = os.getcwd()
            os.chdir(directory)
            pull_command = ['git', 'pull']
            check_call(pull_command)
            os.chdir(cur_dir)
        else:
            clone_command = ['git', 'clone', '-b', branch, url, directory]
            check_call(clone_command)


class BenchmarkReporter(metaclass=ABCMeta):
    @classmethod
    def makeReporter(cls, result_uri, report_uri, report_auth):
        return GitHubReporter(result_uri, report_uri, report_auth)

    @abstractmethod
    def __init__(self):
        pass


class GitHubReporter(BenchmarkReporter):
    def __init__(self, result_uri, report_uri, report_auth):
        self._comments_url = report_uri
        self._comment_username = report_auth.getUsername()
        self._comment_password = report_auth.getPassword()
        self._result_link = result_uri

    def report_run_finished(self):

        self._delete_old_comments()

        comment_body = ("## Automated report from asv run\nBenchmark run "
                        "completed successfully. Results available at\n[%s]"
                        "(%s)") % (self._result_link, self._result_link)
        params = {'body': comment_body}
        requests.post(self._comments_url, data=json.dumps(params),
                      auth=(self._comment_username, self._comment_password))

    def _delete_old_comments(self):
        comments = self._get_comments()
        for comment in comments:
            author = comment['user']['login']
            if author == self._comment_username:
                self._delete_comment(comment['url'])

    def _get_comments(self):
        response = requests.get(self._comments_url)
        return response.json()

    def _delete_comment(self, comment_url):
        requests.delete(comment_url,
                        auth=(self._comment_username, self._comment_password))


