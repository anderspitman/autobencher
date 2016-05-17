from abc import ABCMeta, abstractmethod
from subprocess import check_call


class Publisher(metaclass=ABCMeta):

    @abstractmethod
    def publish(self, dest):
        """Abstract method"""


class ASVPublisher(Publisher):
    def __init__(self, publish_uri):
        self._publish_uri = publish_uri

    def publish(self, dest):
        asv_publish_command = ['asv', 'publish']
        check_call(asv_publish_command)

        uri = '/'.join([self._publish_uri, dest])
        upload_to_s3_command = ['aws', 's3', 'sync', 'html', uri, '--delete']
        check_call(upload_to_s3_command)
