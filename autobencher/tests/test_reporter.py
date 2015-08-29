import sys, os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

from unittest import mock

from reporter import ASVBenchmarkReporter
from util import Authorization

@mock.patch('reporter.check_call')
@mock.patch('reporter.requests')
def test_report_run_started(mock_requests, mock_check_call):
    pass

@mock.patch('reporter.check_call')
@mock.patch('reporter.requests')
def test_report_run_finished(mock_requests, mock_check_call):
    result_uri = 'localhost/results'
    report_uri = 'localhost/report'
    username = 'dummy_user'
    password = 'dummy_pass'
    expected_post = ('{"body": "## Automated report\\nBenchmark run completed '
                     'successfully. Results available '
                     'at\\n[%s](%s)"}') % (result_uri, result_uri)


    auth = Authorization(username, password)
    reporter = ASVBenchmarkReporter(result_uri, report_uri, auth)
    reporter.report()

    mock_requests.get.assert_called_with(report_uri)
    mock_requests.post.assert_called_with(report_uri, data=expected_post,
                                          auth=(username, password))
