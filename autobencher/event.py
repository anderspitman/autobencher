import os

from abc import ABCMeta, abstractmethod


class EventData(object):
    def __init__(self):
        self.reporter_data = ReporterData()
        self.runner_data = RunnerData()

    @property
    def valid(self):
        return self._valid
    @valid.setter
    def valid(self, value):
        self._valid = value

    @property
    def result_uri(self):
        return self._result_uri
    @result_uri.setter
    def result_uri(self, value):
        self._result_uri = value

    @property
    def report_uri(self):
        return self._report_uri
    @report_uri.setter
    def report_uri(self, value):
        self._report_uri = value
        
    @property
    def repository_uri(self):
        return self._repository_uri
    @repository_uri.setter
    def repository_uri(self, value):
        self._repository_uri = value

    @property
    def repository_base(self):
        return self._repository_base
    @repository_base.setter
    def repository_base(self, value):
        self._repository_base = value

    @property
    def branch(self):
        return self._branch
    @branch.setter
    def branch(self, value):
        self._branch = value

    @property
    def branch_owner(self):
        return self._branch_owner
    @branch_owner.setter
    def branch_owner(self, value):
        self._branch_owner = value


class RunnerData(object):
    pass


class ReporterData(object):
    @property
    def result_uri(self):
        return self._result_uri
    @result_uri.setter
    def result_uri(self, value):
        self._result_uri = value

    @property
    def report_uri(self):
        return self._report_uri
    @report_uri.setter
    def report_uri(self, value):
        self._report_uri = value

    @property
    def report_auth(self):
        return self._report_auth
    @report_auth.setter
    def report_auth(self, report_auth):
        self._report_auth = report_auth

    def __init__(self, result_uri=None, report_uri=None, report_auth=None):
        self._result_uri = result_uri
        self._report_uri = report_uri
        self._report_auth = report_auth

    def __eq__(self, other):
        return (self._result_uri == other._result_uri and
                self._report_uri == other._report_uri and
                self._report_auth == other._report_auth)


class EventParser(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, event):
        pass

    @abstractmethod
    def get_event_data(self):
        pass


class GitHubWebhooksParser(EventParser):
    def __init__(self, event):
        pass


class ASVEventParser(GitHubWebhooksParser):
    def __init__(self, event):
        self._event_data = EventData()
        self._event_data.valid = ('pull_request' in event and
                                  event['action'] in ('opened', 'synchronize'))

        if self._event_data.valid:
            hostname = os.environ['HOSTNAME']
            port = os.environ['PORT']

            server = hostname + ':' + port
            link_parts =\
                (server, 'runs',
                 event['pull_request']['head']['repo']['owner']['login'],
                 event['pull_request']['head']['ref'],
                 'html', 'index.html')
            self._event_data.result_uri = os.sep.join(link_parts)
            self._event_data.reporter_data.result_uri = os.sep.join(link_parts)
            self._event_data.report_uri = event['pull_request']['comments_url']
            self._event_data.repository_uri = \
                event['pull_request']['head']['repo']['clone_url']
            self._event_data.runner_data.repository_uri = \
                event['pull_request']['head']['repo']['clone_url']
            self._event_data.repository_base = \
                event['pull_request']['base']['sha']
            self._event_data.branch = \
                event['pull_request']['head']['ref']
            self._event_data.branch_owner = \
                event['pull_request']['head']['repo']['owner']['login']

    def get_event_data(self):
        return self._event_data
