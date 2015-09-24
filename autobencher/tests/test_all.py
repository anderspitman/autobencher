import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import json

from unittest.mock import patch

from autobencher.event import RunnerData, ReporterData, EventData, ASVEventParser
from autobencher.server import process_post
from autobencher.factory import BenchmarkerFactory
from autobencher.util import Authorization

from autobencher.reporter import GitHubReporter, ASVBenchmarkReporter


class TestRunnerData:
    def setup_method(self, test_method):
        self.runner_data = RunnerData()

    def test_simple(self):
        self.runner_data.repository_uri = '/'
        self.runner_data.repository_base = 'master'
        self.runner_data.branch = 'test-branch'
        self.runner_data.branch_owner = 'fake'

        assert self.runner_data.repository_uri == '/'
        assert self.runner_data.repository_base == 'master'
        assert self.runner_data.branch == 'test-branch'
        assert self.runner_data.branch_owner == 'fake'


class TestAuth:
    def test_eq_simple(self):
        user = 'user'
        password = 'pass'
        obs1 = Authorization(user, password)
        obs2 = Authorization(user, password)
        assert obs1 == obs2


class TestReporterData:
    def setup_method(self, test_method):
        self.reporter_data = ReporterData()
        report_user = 'fake-user'
        report_pass = 'fake-pass'

        self.result_uri = '/results'
        self.report_uri = '/report'
        self.report_auth = Authorization(report_user, report_pass)
        self.reporter_data.report_auth = self.report_auth

    def test_simple(self):

        self.reporter_data.result_uri = self.result_uri
        self.reporter_data.report_uri = self.report_uri
        self.reporter_data.report_auth = self.report_auth

        assert self.reporter_data.result_uri == '/results'
        assert self.reporter_data.report_uri == '/report'
        assert self.reporter_data.report_auth == self.report_auth

    def test_formal_parameters(self):
        observed = ReporterData(self.result_uri, self.report_uri, self.report_auth)
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


class TestEventData:
    def setup_method(self, test_method):
        self.event_data = EventData()

    def test(self):
        assert self.event_data.reporter_data is not None
        assert self.event_data.runner_data is not None


class RequestDouble:
    pass

class TestAutobencherPost:
    def setup_method(self, test_method):
        pass

    @patch('autobencher.server.Authorization', autospec=True)
    @patch('autobencher.factory.ASVBenchmarkReporter', autospec=True)
    @patch('autobencher.factory.ASVBenchmarkRunner', autospec=True)
    def test_post(self, MockASVBenchmarkRunner, MockASVBenchmarkReporter,
                  MockAuthorization):
        repository_uri = 'dummy_clone_url'
        login = 'dummy_login'
        branch = 'branch'
        repository_base = 'asdfasdf'

        hostname = '192.168.0.1'
        port = str(8000)
        server = hostname + ':' + port
        link_parts = (server, 'runs', login, branch, 'html', 'index.html')
        result_uri = os.sep.join(link_parts)
        report_uri = 'dummy_comment_url'
        report_username = 'dummy_comment_user'
        report_password = 'dummy_comment_pass'

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
        request = RequestDouble
        request.body = json.dumps(event).encode()
        os.environ['HOSTNAME'] = hostname
        os.environ['PORT'] = port
        os.environ['REPORT_USERNAME'] = report_username
        os.environ['REPORT_PASSWORD'] = report_password

        factory = BenchmarkerFactory.makeFactory()
        process_post(factory, request)

        mock_report_auth = MockAuthorization.return_value
        mock_reporter = MockASVBenchmarkReporter.return_value
        mock_runner = MockASVBenchmarkRunner.return_value

        MockASVBenchmarkRunner.assert_called_with(
            os.getcwd(), repository_uri, repository_base, branch, login,
            mock_reporter)
        assert mock_runner.get_run_location.called
        assert mock_runner.run.called

        MockASVBenchmarkReporter.assert_called_with(
            result_uri, report_uri, mock_report_auth)


class TestMakeReporter:
    def setup_method(self, test_method):
        self.result_uri = 'result_uri' 
        self.report_uri = 'fake_comment_url'
        self.report_user = 'fake_user'
        self.report_pass = 'fake_pass'
        self.report_auth = Authorization(self.report_user, self.report_pass)

        self.event_data = EventData()
        self.event_data.reporter_data.result_uri = self.result_uri

        self.factory = BenchmarkerFactory.makeFactory()

    def test_makes_reporter(self):
        observed = self.factory.makeReporter(self.event_data.reporter_data,
                                             self.report_uri, self.report_auth)
        assert isinstance(observed, ASVBenchmarkReporter)

    def test_equal_to_manually_created(self):
        expected = ASVBenchmarkReporter(self.result_uri, self.report_uri,
                                        self.report_auth)
        observed = self.factory.makeReporter(self.event_data.reporter_data,
                                             self.report_uri, self.report_auth)
        assert expected == observed


class TestGitHubReporter:
    def setup_method(self, test_method):
        self.result_uri = 'result_uri' 
        self.report_uri = 'fake_comment_url'
        self.report_user = 'fake_user'
        self.report_pass = 'fake_pass'
        self.report_auth = Authorization(self.report_user, self.report_pass)

        self.event_data = EventData()
        self.event_data.reporter_data.result_uri = self.result_uri

        self.factory = BenchmarkerFactory.makeFactory()

    def test_eq_simple(self):
        rep1 = GitHubReporter(self.event_data.reporter_data, self.report_uri,
                              self.report_auth)
        rep2 = GitHubReporter(self.event_data.reporter_data, self.report_uri,
                              self.report_auth)
        assert rep1 == rep2

    def test_eq_different_result_uri(self):
        rep1 = GitHubReporter(self.result_uri, self.report_uri,
                              self.report_auth)
        self.event_data.reporter_data.result_uri = 'different'
        rep2 = GitHubReporter(self.event_data.reporter_data.result_uri,
                              self.report_uri, self.report_auth)
        assert rep1 != rep2

    def test_eq_different_report_uri(self):
        rep1 = GitHubReporter(self.result_uri, self.report_uri,
                              self.report_auth)
        self.report_uri = 'different'
        rep2 = GitHubReporter(self.result_uri, self.report_uri,
                              self.report_auth)
        assert rep1 != rep2

    def test_eq_different_auth_user(self):
        rep1 = GitHubReporter(self.result_uri, self.report_uri,
                              self.report_auth)
        auth = Authorization('different', self.report_auth.password)
        rep2 = GitHubReporter(self.event_data.reporter_data.result_uri,
                              self.report_uri, auth)
        assert rep1 != rep2

    def test_eq_different_auth_pass(self):
        rep1 = GitHubReporter(self.result_uri, self.report_uri,
                              self.report_auth)
        auth = Authorization(self.report_auth.username, 'different')
        rep2 = GitHubReporter(self.result_uri, self.report_uri, auth)
        assert rep1 != rep2


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

        hostname = '192.168.0.1'
        port = str(8000)
        server = hostname + ':' + port
        link_parts = (server, 'runs', login, branch, 'html', 'index.html')
        result_uri = os.sep.join(link_parts)
        report_uri = 'dummy_comment_url'
        report_username = 'dummy_comment_user'
        report_password = 'dummy_comment_pass'

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
        exp_reporter_data = ReporterData()
        exp_reporter_data.result_uri = exp_result_uri

        assert event_data.valid
        assert event_data.result_uri == exp_result_uri
        assert event_data.reporter_data == exp_reporter_data
