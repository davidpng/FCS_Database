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
    ('git describe --tags --dirty > FlowAnal/data/ver.tmp'
     '&& mv FlowAnal/data/ver.tmp FlowAnal/data/ver '
     '|| rm -f FlowAnal/data/ver.tmp'),
    shell=True, stderr=open(os.devnull, "w"))

from FlowAnal import __version__
package_data = glob.glob('data/*')

params = {'author': ['David Ng', 'Daniel Herman'],
          'author_email': ['ngdavid@uw.edu', 'hermands@uw.edu'],
          'description': 'Analysis of clinical flow cytometry designed for hematopathology',
          'name': 'FlowAnal',
          'packages': find_packages(),
          'package_dir': {'FlowAnal': 'FlowAnal'},
          'entry_points': {
              'console_scripts': ['runme = FlowAnal.scripts.main:main']
          },
          'version': __version__,
          'package_data': {'FlowAnal': package_data},
          'test_suite': 'tests',
          'cmdclass': {'check_version': CheckVersion}
          }

setup(**params)
