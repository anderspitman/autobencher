from abc import ABCMeta, abstractmethod

from .runner import ASVBenchmarkRunner
from .reporter import ASVBenchmarkReporter

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
    def makeFactory(cls):
        return ASVBenchmarkerFactory()


class ASVBenchmarkerFactory(BenchmarkerFactory):

    @classmethod
    def makeRunner(cls, directory, repo_uri, repo_base, branch, branch_owner,
                   reporter):
        return ASVBenchmarkRunner(directory, repo_uri, repo_base, branch,
                                  branch_owner, reporter)

    @classmethod
    def makeReporter(cls, result_uri, report_uri, report_auth):
        return ASVBenchmarkReporter(result_uri, report_uri, report_auth)
        


