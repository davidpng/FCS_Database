import glob
import os
import subprocess

from distutils.core import Command
from setuptools import setup, find_packages


class CheckVersion(Command):
    description = 'Confirm that the stored package version is correct'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with open('FCS_Database/data/ver') as f:
            stored_version = f.read().strip()

        git_version = subprocess.check_output(
            ['git', 'describe', '--tags', '--dirty']).strip()

        assert stored_version == git_version
        print 'the current version is', stored_version

subprocess.call(
    ('git describe --tags --dirty > FCS_Database/data/ver.tmp'
     '&& mv FCS_Database/data/ver.tmp FCS_Database/data/ver '
     '|| rm -f FCS_Database/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from FCS_Database import __version__
package_data = glob.glob('data/*')

params = {'author': ['David Ng', 'Daniel Herman'],
          'author_email': ['ngdavid@uw.edu', 'hermands@uw.edu'],
          'description': 'Analysis of clinical flow cytometry designed for hematopathology',
          'name': 'FCS_Database',
          'packages': find_packages(),
          'package_dir': {'FCS_Database': 'FCS_Database'},
          'entry_points': {
              'console_scripts': ['runme = FCS_Database.scripts.main:main']
          },
          'version': __version__,
          'package_data': {'FCS_Database': package_data},
          'test_suite': 'tests',
          'cmdclass': {'check_version': CheckVersion}
          }

setup(**params)
