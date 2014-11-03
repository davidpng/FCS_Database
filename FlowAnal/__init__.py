"""
Framework for the FCS_Database
"""
import glob
from os import path


_data = path.join(path.dirname(__file__), 'data')


def package_data(fname, pattern=None):
    """Return the absolute path to a file included in package data,
    raising ValueError if no such file exists. If
    `pattern` is provided, return a list of matching files in package
    data (ignoring `fname`). If directory is listed, look specifically in that directory
    TODO: Make this a little more flexible

    """

    if pattern:
        return glob.glob(path.join(_data, pattern))

    # Look for fname in _data
    pth = path.join(_data, fname)

    if not path.exists(pth):
        raise ValueError('Package data (%s) does not contain the file %s' % (_data, fname))

    return pth

try:
    with open(package_data('ver')) as v:
        ver = v.read().strip()
except Exception, e:
    ver = 'v0.0.0.unknown'

__version__ = ver.lstrip('v')
