import json
import requests

from subprocess import check_call
from abc import ABCMeta, abstractmethod


class BenchmarkReporter(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def report(self):
        pass


class GitHubReporter(BenchmarkReporter):
    def __init__(self, result_uri, report_uri, report_auth):
        self._comments_url = report_uri
        self._comment_username = report_auth.username
        self._comment_password = report_auth.password
        self._result_link = result_uri

    def __eq__(self, other):
        return (self._result_link == other._result_link and
                self._comments_url == other._comments_url and
                self._comment_username == other._comment_username and
                self._comment_password == other._comment_password)

    def report(self):

        self._delete_old_comments()

        comment_body = ("## Automated report\nBenchmark run "
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


class ASVBenchmarkReporter(GitHubReporter):
    def report(self):
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)
        super(ASVBenchmarkReporter, self).report()
