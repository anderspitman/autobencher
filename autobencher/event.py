from abc import ABCMeta, abstractmethod


class EventData(object):
    def __init__(self):
        self.reporter_data = ReporterData()
        self.runner_data = RunnerData()
        self.is_master_update = False

    @property
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        self._valid = value

    @property
    def is_master_update(self):
        return self._is_master_update

    @is_master_update.setter
    def is_master_update(self, value):
        self._is_master_update = value


class RunnerData(object):
    @property
    def repository_uri(self):
        return self._repository_uri

    @repository_uri.setter
    def repository_uri(self, value):
        self._repository_uri = value

    @property
    def master_repository_uri(self):
        return self._master_repository_uri

    @master_repository_uri.setter
    def master_repository_uri(self, value):
        self._master_repository_uri = value

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

    def __init__(self, repository_uri=None, master_repository_uri=None,
                 repository_base=None, branch=None, branch_owner=None):
        self._repository_uri = repository_uri
        self._master_repository_uri = master_repository_uri
        self._repository_base = repository_base
        self._branch = branch
        self._branch_owner = branch_owner

    def __eq__(self, other):
        return (self._repository_uri == other._repository_uri and
                self._repository_base == other._repository_base and
                self._branch == other._branch and
                self._branch_owner == other._branch_owner)


class ReporterData(object):
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

    @property
    def branch(self):
        return self._branch

    @branch.setter
    def branch(self, branch):
        self._branch = branch

    @property
    def branch_owner(self):
        return self._branch_owner

    @branch_owner.setter
    def branch_owner(self, branch_owner):
        self._branch_owner = branch_owner

    def __init__(self, report_uri=None, report_auth=None,
                 branch=None, branch_owner=None):
        self.report_uri = report_uri
        self.report_auth = report_auth
        self.branch = branch
        self._branch_owner = branch_owner

    def __eq__(self, other):
        return (self._report_uri == other._report_uri and
                self._report_auth == other._report_auth and
                self._branch == other._branch and
                self._branch_owner == other._branch_owner)


class EventParser(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, event):
        """Abstract constructor"""

    @abstractmethod
    def get_event_data(self):
        """Abstract method for retrieving event data"""


class GitHubWebhooksParser(EventParser):
    def __init__(self, event):
        self._event_data = EventData()
        self._event_data.valid = self._event_is_valid(event)

        if self._event_data.valid:
            self._event_data.is_master_update = self._is_valid_merge(event)
            branch = event['pull_request']['head']['ref']
            branch_owner = \
                event['pull_request']['head']['repo']['owner']['login']

            self._event_data.reporter_data.branch = branch
            self._event_data.reporter_data.branch_owner = branch_owner

            self._event_data.runner_data.repository_uri = \
                event['pull_request']['head']['repo']['clone_url']
            self._event_data.runner_data.master_repository_uri = \
                event['pull_request']['base']['repo']['clone_url']
            self._event_data.runner_data.repository_base = \
                event['pull_request']['base']['sha']
            self._event_data.runner_data.branch = branch
            self._event_data.runner_data.branch_owner = branch_owner

    def get_event_data(self):
        return self._event_data

    def _is_valid_merge(self, event):
        valid_merge = ('pull_request' in event and
                       event['action'] == 'closed' and
                       event['pull_request']['merged'])
        return valid_merge

    def _event_is_valid(self, event):
        valid_pr = ('pull_request' in event and
                    event['action'] in ('opened', 'synchronize'))
        return valid_pr or self._is_valid_merge(event)


class GitHubCommentEventParser(GitHubWebhooksParser):
    def __init__(self, event):
        super(GitHubCommentEventParser, self).__init__(event)

        if self._event_data.valid:
            self._event_data.reporter_data.report_uri = \
                event['pull_request']['comments_url']


class GitHubStatusEventParser(GitHubWebhooksParser):
    def __init__(self, event):
        super(GitHubStatusEventParser, self).__init__(event)

        if self._event_data.valid:
            self._event_data.reporter_data.report_uri = \
                event['pull_request']['statuses_url']


class ASVEventParser(GitHubStatusEventParser):
    pass
