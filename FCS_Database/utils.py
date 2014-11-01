""" Common utilities placeholder """
from subprocess import Popen, PIPE
from git import Repo
import glob
from os import path


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


def package_data(fname, dir=None, pattern=None):
    """Return the absolute path to a file included in package data,
    raising ValueError if no such file exists. If
    `pattern` is provided, return a list of matching files in package
    data (ignoring `fname`). If directory is listed, look specifically in that directory
    TODO: Make this a little more flexible

    """
    # Pick directory
    if dir is not None:
        _data = path.join(path.dirname(__file__), dir)
    else:
        _data = path.dirname(__file__)

    # Use pattern if provided
    if pattern:
        return glob.glob(path.join(_data, pattern))

    # Look for fname in _data
    pth = path.join(_data, fname)
    if not path.exists(pth):
        raise ValueError('Package data (%s) does not contain the file %s' % (_data, fname))
    return pth


class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
