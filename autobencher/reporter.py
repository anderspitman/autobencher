import os
import json
import requests

from subprocess import check_call
from abc import ABCMeta, abstractmethod


class BenchmarkReporter(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        """Abstract constructor"""

    @abstractmethod
    def report(self):
        """Abstract method for reporting"""


class GitHubReporter(BenchmarkReporter):
    def __init__(self, result_uri, report_uri, branch, branch_owner,
                 report_auth):
        self._comments_url = report_uri
        self._comment_username = report_auth.username
        self._comment_password = report_auth.password

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
                self._comments_url == other._comments_url and
                self._comment_username == other._comment_username and
                self._comment_password == other._comment_password)

    def report(self):

        self._delete_old_comments()

        comment_body = ("## Automated report\nBenchmark run "
                        "completed successfully. Results available [here]"
                        "(%s)") % (self._result_link)
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


class ASVBenchmarkReporter(GitHubReporter):
    def report(self):
        self._publish()
        super(ASVBenchmarkReporter, self).report()

    def _publish(self):
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)


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
