import os
from abc import ABCMeta, abstractmethod

from .runner import ASVBenchmarkRunner
from .reporter import ASVBenchmarkReporter
from .event import ASVEventParser


class BenchmarkerFactory(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def makeRunner(cls):
        """Abstract method for creating runners"""

    @classmethod
    @abstractmethod
    def makeReporter(cls):
        """Abstract method for creating reporters"""

    @classmethod
    @abstractmethod
    def makeEventParser(cls):
        """Abstract method for creating event parsers"""

    @classmethod
    def makeFactory(cls):
        return ASVBenchmarkerFactory()


class ASVBenchmarkerFactory(BenchmarkerFactory):

    @classmethod
    def makeRunner(cls, directory, data, reporter):
        return ASVBenchmarkRunner(directory, data.repository_uri,
                                  data.repository_base, data.branch,
                                  data.branch_owner, reporter)

    @classmethod
    def makeReporter(cls, data, report_auth, result_address):
        link_parts =\
            (result_address, 'runs',
             data.branch_owner,
             data.branch,
             'html', 'index.html')
        result_uri = os.sep.join(link_parts)
        return ASVBenchmarkReporter(result_uri, data.report_uri,
                                    report_auth)

    @classmethod
    def makeEventParser(cls, event):
        return ASVEventParser(event)
