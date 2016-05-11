import os
import json
import requests
import asv

from subprocess import check_call
from abc import ABCMeta, abstractmethod


class BenchmarkReporter(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        """Abstract constructor"""

    @abstractmethod
    def report(self):
        """Abstract method for reporting"""

    @abstractmethod
    def report_started(self):
        """Abstract method for reporting benchmarking started"""


class GitHubReporter(BenchmarkReporter):
    def __init__(self, report_uri, branch, branch_owner, report_auth):
        self._report_uri = report_uri
        self._report_username = report_auth.username
        self._report_password = report_auth.password

        s3_host = 'https://s3-us-west-2.amazonaws.com'
        s3_link_parts = (s3_host, 'scikit-bio.org', 'benchmarks',
                         'pull_requests',
                         branch_owner, branch, 'index.html')
        s3_url = '/'.join(s3_link_parts)

        self._result_link = s3_url

        self._branch = branch
        self._branch_owner = branch_owner

    def __eq__(self, other):
        return (self._result_link == other._result_link and
                self._report_uri == other._report_uri and
                self._report_username == other._report_username and
                self._report_password == other._report_password)

    @abstractmethod
    def report(self):
        """Abstract method for reporting"""

    @abstractmethod
    def report_started(self):
        """Abstract method for reporting benchmarking started"""


class GitHubStatusReporter(GitHubReporter):
    def __init__(self, result_uri, report_uri, branch, branch_owner,
                 report_auth):

        super(GitHubStatusReporter, self).__init__(
            report_uri, branch, branch_owner, report_auth)

    def report(self):
        params = self._build_params('success')

        requests.post(self._report_uri, data=json.dumps(params),
                      auth=(self._report_username, self._report_password))

    def report_started(self):
        """Abstract method for reporting benchmarking started"""
        params = {
            'state': 'pending',
            'description': "ASV benchmark run started",
            'context': "ASV Benchmarks"
        }


        requests.post(self._report_uri, data=json.dumps(params),
                      auth=(self._report_username, self._report_password))

    def _build_params(self, success_string):
        return {
            'state': success_string,
            'target_url': self._result_link,
            'description': "ASV benchmark run completed successfully",
            'context': "ASV Benchmarks"
        }


class GitHubCommentReporter(GitHubReporter):
    def __init__(self, result_uri, report_uri, branch, branch_owner,
                 report_auth):

        super(GitHubCommentReporter, self).__init__(
            report_uri, branch, branch_owner, report_auth)

    def report(self):

        self._delete_old_report_comments()

        comment_body = ("## Automated report\nBenchmark run "
                        "completed successfully. Results available [here]"
                        "(%s)") % (self._result_link)
        params = {'body': comment_body}
        requests.post(self._report_uri, data=json.dumps(params),
                      auth=(self._report_username, self._report_password))

    def _delete_old_report_comments(self):
        comments = self._get_comments()
        for comment in comments:
            author = comment['user']['login']
            if author == self._report_username:
                self._delete_comment(comment['url'])

    def _get_comments(self):
        response = requests.get(self._report_uri)
        return response.json()

    def _delete_comment(self, comment_url):
        requests.delete(comment_url,
                        auth=(self._report_username, self._report_password))


class ASVBenchmarkReporter(GitHubStatusReporter):
    def report(self):
        self._publish()

        path = 'results'

        results_list = list(asv.results.iter_results(path)) 

        regression = False
        if len(results_list) > 0:

            # first commit chronologically should be master; last should be the
            # tip of the branch
            results_list = sorted(results_list, key=lambda result: result.date)
            master_commit_hash = results_list[0].commit_hash
            tip_commit_hash = results_list[-1].commit_hash

            master_results = {}
            tip_results = {}

            for results in asv.results.iter_results(path):
                for key, val in results.params.items():
                    configuration = \
                        self._generate_unique_configuration_string(results)
                    
                    if results.commit_hash == master_commit_hash:
                        if configuration not in master_results:
                            master_results[configuration] = results.results
                    elif results.commit_hash == tip_commit_hash:
                        if configuration not in tip_results:
                            tip_results[configuration] = results.results

            for configuration in tip_results:
                for benchmark, value in tip_results[configuration].items():
                    # if this benchmark exists on master
                    if benchmark in master_results[configuration]:
                        master_val = master_results[configuration][benchmark]
                        tip_val = value
                        regression = self._has_regression(master_val, tip_val)
                        
                        if regression:
                            break
                if regression:
                    break

        if regression:
            params = {
                'state': 'failure',
                'target_url': self._result_link,
                'description': "ASV benchmark run detected a regression",
                'context': "ASV Benchmarks"
            }
            res = requests.post(self._report_uri, data=json.dumps(params),
                          auth=(self._report_username, self._report_password))

        else:
            super(ASVBenchmarkReporter, self).report()

    def _publish(self):
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)

    def _generate_unique_configuration_string(self, results):
        return results._env_name

    def _has_regression(self, master_val, tip_val):
        return ((tip_val - master_val) / master_val) > .2


class ASVRemoteBenchmarkReporter(ASVBenchmarkReporter):
    def _publish(self):

        super(ASVRemoteBenchmarkReporter, self)._publish()

        s3_upload_url_parts = ('s3://scikit-bio.org', 'benchmarks',
                               'pull_requests', self._branch_owner,
                               self._branch)
        s3_upload_url = os.sep.join(s3_upload_url_parts)
        upload_to_s3_command = ['aws', 's3', 'sync', 'html', s3_upload_url,
                                '--delete']
        check_call(upload_to_s3_command)
