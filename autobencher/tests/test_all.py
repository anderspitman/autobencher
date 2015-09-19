import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

import json

from unittest.mock import patch

from autobencher.event import RunnerData, ReporterData, EventData
from autobencher.server import process_post
from autobencher.factory import BenchmarkerFactory


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


class TestReporterData:
    def setup_method(self, test_method):
        self.reporter_data = ReporterData()

    def test_simple(self):
        self.reporter_data.result_uri = '/results'
        self.reporter_data.report_uri = '/report'

        assert self.reporter_data.result_uri == '/results'
        assert self.reporter_data.report_uri == '/report'


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
