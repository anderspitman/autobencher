import testing_import_hack

from autobencher.event import (RunnerData, ReporterData, EventData,
                               ASVEventParser)
from autobencher.util import Authorization


testing_import_hack.use_package_so_flake8_is_happy()


class TestReporterData:
    def setup_method(self, test_method):
        self.reporter_data = ReporterData()
        report_user = 'fake-user'
        report_pass = 'fake-pass'

        self.result_uri = '/results'
        self.report_uri = '/report'
        self.report_auth = Authorization(report_user, report_pass)
        self.reporter_data.report_auth = self.report_auth

    def test_init_empty_all_none(self):
        obs = ReporterData()
        assert obs.result_uri is None
        assert obs.report_uri is None
        assert obs.report_auth is None

    def test_simple(self):

        self.reporter_data.result_uri = self.result_uri
        self.reporter_data.report_uri = self.report_uri
        self.reporter_data.report_auth = self.report_auth

        assert self.reporter_data.result_uri == '/results'
        assert self.reporter_data.report_uri == '/report'
        assert self.reporter_data.report_auth == self.report_auth

    def test_formal_parameters(self):
        observed = ReporterData(self.result_uri, self.report_uri,
                                self.report_auth)
        assert observed.result_uri == self.result_uri
        assert observed.report_uri == self.report_uri
        assert observed.report_auth == self.report_auth

    def test_eq_empty(self):
        obs1 = ReporterData()
        obs2 = ReporterData()
        assert obs1 == obs2

    def test_eq_different_results_uri(self):
        obs1 = ReporterData('different', self.report_uri, self.report_auth)
        obs2 = ReporterData(self.result_uri, self.report_uri, self.report_auth)
        assert obs1 != obs2

    def test_eq_different_report_uri(self):
        obs1 = ReporterData(self.result_uri, 'different', self.report_auth)
        obs2 = ReporterData(self.result_uri, self.report_uri, self.report_auth)
        assert obs1 != obs2

    def test_eq_different_auth_user(self):
        auth = Authorization('different', self.report_auth.password)
        obs1 = ReporterData(self.result_uri, self.report_uri, auth)
        obs2 = ReporterData(self.result_uri, self.report_uri, self.report_auth)
        assert obs1 != obs2

    def test_eq_different_auth_pass(self):
        auth = Authorization(self.report_auth.username, 'different')
        obs1 = ReporterData(self.result_uri, self.report_uri, auth)
        obs2 = ReporterData(self.result_uri, self.report_uri, self.report_auth)
        assert obs1 != obs2


class TestRunnerData:
    def setup_method(self, test_method):
        self.runner_data = RunnerData()
        self.directory = '/'
        self.repo_uri = '/repo_uri'
        self.repo_base = 'master'
        self.branch = 'fake-branch'
        self.branch_owner = 'Frank'
        self.reporter = None

    def test_init_empty_all_none(self):
        obs = RunnerData()
        assert obs.repository_uri is None
        assert obs.repository_base is None
        assert obs.branch is None
        assert obs.branch_owner is None

    def test_setters(self):
        self.runner_data.repository_uri = self.repo_uri
        self.runner_data.repository_base = self.repo_base
        self.runner_data.branch = self.branch
        self.runner_data.branch_owner = self.branch_owner

        assert self.runner_data.repository_uri == self.repo_uri
        assert self.runner_data.repository_base == self.repo_base
        assert self.runner_data.branch == self.branch
        assert self.runner_data.branch_owner == self.branch_owner

    def test_formal_parameters(self):
        obs = RunnerData(self.repo_uri, self.repo_base,
                         self.branch, self.branch_owner)
        assert obs.repository_uri == self.repo_uri
        assert obs.repository_base == self.repo_base
        assert obs.branch == self.branch
        assert obs.branch_owner == self.branch_owner

    def test_eq_empty(self):
        obs1 = RunnerData()
        obs2 = RunnerData()
        assert obs1 == obs2

    def test_eq_different_repo_uri(self):
        obs1 = RunnerData(self.repo_uri, self.repo_base,
                          self.branch, self.branch_owner)
        obs2 = RunnerData('different', self.repo_base,
                          self.branch, self.branch_owner)
        assert obs1 != obs2

    def test_eq_different_repo_base(self):
        obs1 = RunnerData(self.repo_uri, self.repo_base,
                          self.branch, self.branch_owner)
        obs2 = RunnerData(self.repo_uri, 'different',
                          self.branch, self.branch_owner)
        assert obs1 != obs2

    def test_eq_different_branch(self):
        obs1 = RunnerData(self.repo_uri, self.repo_base,
                          self.branch, self.branch_owner)
        obs2 = RunnerData(self.repo_uri, self.repo_base,
                          'different', self.branch_owner)
        assert obs1 != obs2

    def test_eq_different_branch_owner(self):
        obs1 = RunnerData(self.repo_uri, self.repo_base,
                          self.branch, self.branch_owner)
        obs2 = RunnerData(self.repo_uri, self.repo_base,
                          self.branch, 'different')
        assert obs1 != obs2


class TestEventData:
    def setup_method(self, test_method):
        self.event_data = EventData()

    def test(self):
        assert self.event_data.reporter_data is not None
        assert self.event_data.runner_data is not None


class TestASVEventParser:
    def setup_method(self, test_method):
        pass

    def test_formal_parameters(self):
        event = {}
        ASVEventParser(event)

    def test_simple(self):
        repository_uri = 'dummy_clone_url'
        login = 'dummy_login'
        branch = 'branch'
        repository_base = 'asdfasdf'

        report_uri = 'dummy_comment_url'

        event = {
            'action': 'opened',
            'pull_request': {
                'head': {
                    'repo': {
                        'clone_url': repository_uri,
                        'owner': {
                            'login': login
                        }
                    },
                    'ref': branch
                },
                'comments_url': report_uri,
                'base': {
                    'sha': repository_base
                }
            }
        }

        parser = ASVEventParser(event)
        event_data = parser.get_event_data()
        exp_result_uri = ('192.168.0.1:8000/runs/dummy_login/'
                          'branch/html/index.html')
        exp_reporter_data = ReporterData(exp_result_uri, report_uri)
        exp_runner_data = RunnerData(repository_uri, repository_base, branch,
                                     branch_owner=login)

        assert event_data.valid
        assert event_data.reporter_data == exp_reporter_data
        assert event_data.runner_data == exp_runner_data
