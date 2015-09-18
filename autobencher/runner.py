import json
import os
import shutil

from multiprocessing import Process
from subprocess import check_call
from abc import ABCMeta, abstractmethod

from .repository import SourceRepository


class BenchmarkRunner(metaclass=ABCMeta):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def get_run_location(self):
        pass


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


class ASVProcess(Process):
    def __init__(self, directory, repo_uri, repo_base, branch,
                 branch_owner, reporter):
        super(ASVProcess, self).__init__()
        self._dir = directory
        self._base_commit = repo_base
        self._branch_ref = branch
        run_dir = os.path.join(self._dir, 'runs')
        owner = branch_owner
        self._branch_dir = os.path.join(run_dir, owner, self._branch_ref)
        self._clone_url = repo_uri
        self._reporter = reporter

        if not os.path.exists(self._branch_dir):
            os.makedirs(self._branch_dir)


    def run(self):
        self._run_asv()

    def get_branch_directory(self):
        return self._branch_dir
       
    def _run_asv(self):
        self._set_up_environment()
        # include 1 previous commit from master so we can see any regressions
        commit_range = self._base_commit + '~1..' + self._branch_ref
        asv_command = ['asv', 'run', '--steps', '10', commit_range]
        #check_call(asv_command)
        self._reporter.report()
        os.chdir(self._dir)

    def _set_up_environment(self):

        self._source_repo = os.path.join(self._branch_dir, 'source_repo')
        self._repo = SourceRepository.makeRepository(self._clone_url,
                                                     self._branch_ref,
                                                     self._source_repo)

        source_config = os.path.join(self._source_repo, 'asv.conf.json')
        with open(source_config) as asv_fp:
            asv_config = json.load(asv_fp)
        asv_config['repo'] = self._clone_url
        asv_config['branches'] = [self._branch_ref]

        benchmark_dest = os.path.join(self._branch_dir, 'benchmarks')
        if os.path.exists(benchmark_dest):
            shutil.rmtree(benchmark_dest)
        benchmark_source = os.path.join(self._source_repo, 'benchmarks')
        shutil.copytree(benchmark_source, benchmark_dest)
        os.chdir(self._branch_dir)
        with open('asv.conf.json', 'w') as asv_fp:
            json.dump(asv_config, asv_fp, indent=4, sort_keys=True)


