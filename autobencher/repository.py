import os

from subprocess import check_call, check_output
from abc import ABCMeta, abstractmethod


class SourceRepository(metaclass=ABCMeta):
    @classmethod
    def makeRepository(cls, url, branch, directory):
        return GitRepository(url, branch, directory)

    @abstractmethod
    def __init__(self):
        """Abstract constructor"""

    @abstractmethod
    def get_commit_hashes(self):
        """Abstract method"""


class GitRepository(SourceRepository):
    def __init__(self, url, branch, directory):

        self._directory = os.path.abspath(directory)

        if os.path.exists(directory):
            cur_dir = os.getcwd()
            os.chdir(directory)
            pull_command = ['git', 'pull']
            check_call(pull_command)
            os.chdir(cur_dir)
        else:
            clone_command = ['git', 'clone', '-b', branch, url, directory]
            check_call(clone_command)

    def get_commit_hashes(self, branch='master'):
        cur_dir = os.getcwd()
        os.chdir(self._directory)
        command = ['git', 'rev-list', '--first-parent', branch]
        output = check_output(command)
        os.chdir(cur_dir)
        return output.decode('utf-8').strip().split()
