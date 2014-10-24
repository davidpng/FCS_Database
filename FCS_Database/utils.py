""" Common utilities placeholder """
from subprocess import Popen, PIPE
from git import Repo


class GetVersion(object):
    """ Identify the version number of this code for traceability """

    def __init__(self):
        # If git repository
        self.version = self.load_git_version()

    def load_git_version(self):
        """ Get version of current git repository """

        p = Popen(['echo $(git rev-parse --show-toplevel)'], stderr=PIPE, stdout=PIPE, shell=True)
        repos_directory, err = p.communicate()

        if err:
            raise 'Cannot locate git repository directory'

        repo = Repo(repos_directory.strip())
        repo.config_reader()  # Set as read-only access
        if repo.bare is True:
            raise "Repository %s is bare!" % repos_directory

        return repo.head.commit.hexsha[0:7]
