"""
Framework for the FCS_Database
"""

from utils import package_data

try:
    with open(package_data('ver')) as v:
        ver = v.read().strip()
except Exception, e:
    ver = 'v0.0.0.unknown'

__version__ = ver.lstrip('v')
