from abc import ABCMeta, abstractmethod

from .runner import ASVBenchmarkRunner
from .reporter import ASVBenchmarkReporter
from .event import ASVEventParser

class BenchmarkerFactory(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def makeRunner(cls):
        pass

    @classmethod
    @abstractmethod
    def makeReporter(cls):
        pass

    @classmethod
    @abstractmethod
    def makeEventParser(cls):
        pass

    @classmethod
    def makeFactory(cls):
        return ASVBenchmarkerFactory()


class ASVBenchmarkerFactory(BenchmarkerFactory):

    @classmethod
    def makeRunner(cls, directory, repo_uri, repo_base, branch, branch_owner,
                   reporter):
        return ASVBenchmarkRunner(directory, repo_uri, repo_base, branch,
                                  branch_owner, reporter)

    @classmethod
    def makeReporter(cls, data, report_uri, report_auth):
        return ASVBenchmarkReporter(data.result_uri, report_uri, report_auth)

    @classmethod
    def makeEventParser(cls, event):
        return ASVEventParser(event)
        


