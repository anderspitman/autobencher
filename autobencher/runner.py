import json
import os
import shutil

from multiprocessing import Process
from subprocess import call, check_call
from abc import ABCMeta, abstractmethod

from .repository import SourceRepository


class BenchmarkRunner(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        """Abstract method for running"""

    @abstractmethod
    def get_run_location(self):
        """Abstract method for getting the location where the runner is
           working"""

class ASVMasterBenchmarkRunner(BenchmarkRunner):
    def __init__(self, directory, repo_uri):
        self._asv_proc = ASVMasterProcess(directory, repo_uri)

    def run(self):
        self._asv_proc.start()

    def get_run_location(self):
        return ''


class ASVBenchmarkRunner(BenchmarkRunner):
    def __init__(self, directory, repo_uri, repo_base, branch, branch_owner,
                 reporter):
        # Start a new process. This is necessary since we need to change
        # the working directory for ASV to work, but we also need to be able
        # to handle concurrent ASV runs.
        self._asv_proc = ASVProcess(directory, repo_uri, repo_base, branch,
                                    branch_owner, reporter)

    def run(self):
        self._asv_proc.start()

    def get_run_location(self):
        return self._asv_proc.get_branch_directory()


class RunnerProcess(Process):
    def __init__(self, directory, repo_uri):

        self._dir = directory
        self._run_dir = os.path.join(self._dir, 'runs')
        self._clone_url = repo_uri

        self._set_branch_dir()

        if not os.path.exists(self._branch_dir):
            os.makedirs(self._branch_dir)

        self._source_repo = os.path.join(self._branch_dir, 'source_repo')
        self._repo = SourceRepository.makeRepository(self._clone_url,
                                                     self._branch_ref,
                                                     self._source_repo)

        source_config = os.path.join(self._source_repo, 'asv.conf.json')
        with open(source_config) as asv_fp:
            asv_config = json.load(asv_fp)
        asv_config['repo'] = self._clone_url
        asv_config['branches'] = [self._branch_ref]
        dest_config = os.path.join(self._branch_dir, 'asv.conf.json')
        with open(dest_config, 'w') as asv_fp:
            json.dump(asv_config, asv_fp, indent=4, sort_keys=True)

        benchmark_dest = os.path.join(self._branch_dir, 'benchmarks')
        if os.path.exists(benchmark_dest):
            shutil.rmtree(benchmark_dest)
        benchmark_source = os.path.join(self._source_repo, 'benchmarks')
        shutil.copytree(benchmark_source, benchmark_dest)

        super(RunnerProcess, self).__init__()

    @abstractmethod
    def _set_branch_dir(self):
        pass


class ASVMasterProcess(RunnerProcess):
    def __init__(self, directory, repo_uri):

        self._branch_ref = 'master'

        super(ASVMasterProcess, self).__init__(directory, repo_uri)

    def run(self):
        self._run_asv()

    def _run_asv(self):

        os.chdir(self._branch_dir)

        print(os.getcwd())
        asv_command = ['asv', 'run', 'NEW']
        return_code = call(asv_command)

        os.chdir(self._dir)

    def _set_branch_dir(self):
        self._branch_dir = os.path.join(self._run_dir, self._branch_ref)



class ASVProcess(RunnerProcess):
    def __init__(self, directory, repo_uri, repo_base, branch,
                 branch_owner, reporter):

        self._owner = branch_owner
        self._branch_ref = branch

        super(ASVProcess, self).__init__(directory, repo_uri)

        self._base_commit = repo_base

        self._reporter = reporter

    def run(self):
        self._run_asv()

    def get_branch_directory(self):
        return self._branch_dir

    def _run_asv(self):
        self._reporter.report_started()

        os.chdir(self._branch_dir)

        # include 1 previous commit from master so we can see any regressions
        commit_range = self._base_commit + '~1..' + self._branch_ref
        asv_command = ['asv', 'run', '--steps', '10', commit_range]
        check_call(asv_command)
        self._reporter.report()

        os.chdir(self._dir)


    def _set_branch_dir(self):
        self._branch_dir = os.path.join(self._run_dir, self._owner,
                                        self._branch_ref)
