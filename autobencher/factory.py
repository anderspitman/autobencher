from abc import ABCMeta, abstractmethod

from .runner import ASVBenchmarkRunner, ASVMasterBenchmarkRunner
from .reporter import ASVRemoteBenchmarkReporter
from .event import ASVEventParser


class BenchmarkerFactory(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def makeRunner(cls):
        """Abstract method for creating runners"""

    @classmethod
    @abstractmethod
    def make_master_runner(cls):
        """Abstract method for creating master runners"""

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
    def make_master_runner(cls, directory, data):
        return ASVMasterBenchmarkRunner(directory, data.repository_uri)

    @classmethod
    def makeRunner(cls, directory, data, reporter):
        return ASVBenchmarkRunner(directory, data.repository_uri,
                                  data.repository_base, data.branch,
                                  data.branch_owner, reporter)

    @classmethod
    def makeReporter(cls, data, report_auth, result_address):
        return ASVRemoteBenchmarkReporter(result_address, data.report_uri,
                                          data.branch, data.branch_owner,
                                          report_auth)

    @classmethod
    def makeEventParser(cls, event):
        return ASVEventParser(event)
