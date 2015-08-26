import os

from subprocess import check_call
from abc import ABCMeta, abstractmethod


class SourceRepository(metaclass=ABCMeta):
    @classmethod
    def makeRepository(cls, url, branch, directory):
        return GitRepository(url, branch, directory)

    @abstractmethod
    def __init__(self):
        pass


class GitRepository(SourceRepository):
    def __init__(self, url, branch, directory):
        if os.path.exists(directory):
            cur_dir = os.getcwd()
            os.chdir(directory)
            pull_command = ['git', 'pull']
            check_call(pull_command)
            os.chdir(cur_dir)
        else:
            clone_command = ['git', 'clone', '-b', branch, url, directory]
            check_call(clone_command)
