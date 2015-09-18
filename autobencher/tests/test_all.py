import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../../')

from autobencher.event import RunnerData, ReporterData, EventData
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


#class TestMakeEventParser:
#    def test(self):
#        event = {
#            'action': 'opened',
#            'pull_request': {
#            }
#        }
#        factory = BenchmarkerFactory.makeFactory()
#        parser = factory.makeEventParser(event)
#        event_data = parser.getEventData()
#
#        runner_data = event_data.runner_data
#
#        assert runner_data.repository_uri == '/repo_uri'

class TestAutobencherPost:
    def setup_method(self, test_method):
        pass

    def test_post(self):
        pass
