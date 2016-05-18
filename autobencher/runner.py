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
    def __init__(self, directory, repo_uri, publisher):
        self._asv_proc = ASVMasterProcess(directory, repo_uri, publisher)

    def run(self):
        self._asv_proc.start()

    def get_run_location(self):
        return ''


class ASVBenchmarkRunner(BenchmarkRunner):
    def __init__(self, directory, repo_uri, repo_base, branch, branch_owner,
                 reporter, publisher):
        # Start a new process. This is necessary since we need to change
        # the working directory for ASV to work, but we also need to be able
        # to handle concurrent ASV runs.
        self._asv_proc = ASVProcess(directory, repo_uri, repo_base, branch,
                                    branch_owner, reporter, publisher)

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
    def __init__(self, directory, repo_uri, publisher):

        self._branch_ref = 'master'
        self._publisher = publisher

        super(ASVMasterProcess, self).__init__(directory, repo_uri)

    def run(self):
        self._run_asv()

    def _run_asv(self):

        os.chdir(self._branch_dir)

        asv_command = ['asv', 'run', 'NEW']
        call(asv_command)

        self._publisher.publish('master')

        os.chdir(self._dir)

    def _set_branch_dir(self):
        self._branch_dir = os.path.join(self._run_dir, self._branch_ref)


class ASVProcess(RunnerProcess):
    def __init__(self, directory, repo_uri, repo_base, branch,
                 branch_owner, reporter, publisher):

        self._owner = branch_owner
        self._branch_ref = branch

        super(ASVProcess, self).__init__(directory, repo_uri)

        self._base_commit = repo_base
        self._results_dir = os.path.join(self._branch_dir, 'results')

        self._reporter = reporter
        self._publisher = publisher

    def run(self):
        self._run_asv()

    def get_branch_directory(self):
        return self._branch_dir

    def _run_asv(self):
        self._reporter.report_started()

        os.chdir(self._branch_dir)

        self._copy_master_results()

        # run for commits after master
        asv_command = ['asv', 'run', 'NEW']
        call(asv_command)

        if not self._has_regressions():
            self._reporter.report_success()
        else:
            self._reporter.report_failure()

        publish_dest = '/'.join(['pull_requests', self._owner,
                                 self._branch_ref])
        self._publisher.publish(publish_dest)

        os.chdir(self._dir)

    def _has_regressions(self):
        path = self._results_dir

        results_list = list(self._iter_results(path))

        regression = False
        if len(results_list) > 0:

            # first commit chronologically should be master; last should be the
            # tip of the branch
            results_list = sorted(results_list,
                                  key=lambda result: result['date'])
            master_commit_hash = self._base_commit
            tip_commit_hash = results_list[-1]['commit_hash']

            master_results = {}
            tip_results = {}

            for results in self._iter_results(path):
                for key, val in results['params'].items():
                    configuration = \
                        self._generate_unique_configuration_string(results)

                    if results['commit_hash'] == master_commit_hash:
                        if configuration not in master_results:
                            master_results[configuration] = results['results']
                    elif results['commit_hash'] == tip_commit_hash:
                        if configuration not in tip_results:
                            tip_results[configuration] = results['results']

            for configuration in tip_results:
                for benchmark, value in tip_results[configuration].items():
                    # if this benchmark exists on master
                    if benchmark in master_results[configuration]:
                        master_val = master_results[configuration][benchmark]
                        tip_val = value
                        regression = self._is_regression(master_val, tip_val)

                        if regression:
                            break
                if regression:
                    break

        return regression

    # this method was adapted from asv's codebase, in the results.py file
    def _iter_results(self, results_dir):
        skip_files = set([
            'machine.json', 'benchmarks.json'
        ])
        for root, dirs, files in os.walk(results_dir):
            for filename in files:
                if filename not in skip_files and filename.endswith('.json'):
                    path = os.path.join(root, filename)
                    with open(path) as json_file:
                        data = json.load(json_file)
                        yield data

    def _generate_unique_configuration_string(self, results):
        return results['env_name']

    def _is_regression(self, master_val, tip_val):
        # Detect if more than 1/3 slower
        return ((tip_val - master_val) / master_val) > .3333

    def _copy_master_results(self):
        master_results_dir = os.path.join(self._run_dir, 'master',
                                          'results')
        self._results_dir = os.path.join(self._branch_dir, 'results')
        if not os.path.exists(self._results_dir):
            os.makedirs(self._results_dir)

        copy_command = ['rsync', '-av', master_results_dir,
                        self._results_dir]
        check_call(copy_command)

    def _set_branch_dir(self):
        self._branch_dir = os.path.join(self._run_dir, self._owner,
                                        self._branch_ref)
