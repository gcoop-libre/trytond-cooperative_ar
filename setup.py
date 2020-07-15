#!/usr/bin/env python
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

import re
import os
import io
from configparser import ConfigParser
from setuptools import setup, find_packages


def read(fname, slice=None):
    content = io.open(
        os.path.join(os.path.dirname(__file__), fname),
        'r', encoding='utf-8').read()
    if slice:
        content = '\n'.join(content.splitlines()[slice])
    return content


def get_require_version(name):
    if minor_version % 2:
        require = '%s >= %s.%s.dev0, < %s.%s'
    else:
        require = '%s >= %s.%s, < %s.%s'
    require %= (name, major_version, minor_version,
        major_version, minor_version + 1)
    return require


config = ConfigParser()
config.read_file(open(os.path.join(os.path.dirname(__file__), 'tryton.cfg')))
info = dict(config.items('tryton'))
for key in ('depends', 'extras_depend', 'xml'):
    if key in info:
        info[key] = info[key].strip().splitlines()
version = info.get('version', '0.0.1')
major_version, minor_version, _ = version.split('.', 2)
major_version = int(major_version)
minor_version = int(minor_version)
name = 'trytonar_cooperative_ar'

download_url = 'https://github.com/gcoop-libre/trytond-cooperative_ar/tree/%s.%s' % (
    major_version, minor_version)
if minor_version % 2:
    version = '%s.%s.dev0' % (major_version, minor_version)
    download_url = (
        'git+http://github.com/gcoop-libre/%s#egg=%s-%s' % (
            name.replace('trytonar','trytond'), name, version))
local_version = []
for build in ['CI_BUILD_NUMBER', 'CI_JOB_NUMBER', 'CI_JOB_ID']:
    if os.environ.get(build):
        local_version.append(os.environ[build])
if local_version:
    version += '+' + '.'.join(local_version)

requires = []
for dep in info.get('depends', []):
    if dep == 'party_ar':
        requires.append('trytonar_party_ar @ git+https://github.com/tryton-ar/party_ar.git@%s.%s#egg=trytonar_party_ar-%s.%s' % (major_version, minor_version, major_version, minor_version))
    elif dep == 'analytic_account_chart_template':
        requires.append('trytonar_analytic_account_chart_template @ git+https://github.com/gcoop-libre/trytond-analytic_account_chart_template.git@%s.%s#egg=trytonar_analytic_account_chart_template-%s.%s' % (major_version, minor_version, major_version, minor_version))
    elif dep == 'account_coop_ar':
        requires.append('trytonar_account_coop_ar @ git+https://github.com/gcoop-libre/trytond-account_coop_ar.git@%s.%s#egg=trytonar_account_coop-ar-%s.%s' % (major_version, minor_version, major_version, minor_version))
    elif dep == 'bank_ar':
        requires.append('trytonar_bank_ar @ git+https://github.com/tryton-ar/bank_ar.git@%s.%s#egg=trytonar_bank_ar-%s.%s' % (major_version, minor_version, major_version, minor_version))
    elif not re.match(r'(ir|res)(\W|$)', dep):
        requires.append(get_require_version('trytond_%s' % dep))
requires.append(get_require_version('trytond'))
requires.append('httplib2')
requires.append('singing-girl')
requires.append('python-stdnum')
requires.append('pyafipws @ git+https://github.com/reingart/pyafipws.git@py3k#egg=pyafipws-py3k')
requires.append('pysimplesoap @ git+https://github.com/pysimplesoap/pysimplesoap.git@stable_py3k#egg=pysimplesoap-stable_py3k')
# requires.append('werkzeug<1.0')

tests_require = [get_require_version('proteus')]
dependency_links = [
    'https://github.com/tryton-ar/party_ar/tarball/%s.%s#egg=trytonar_party_ar-%s.%s' \
        % (major_version, minor_version, major_version, minor_version),
    'https://github.com/tryton-ar/bank_ar/tarball/%s.%s#egg=trytonar_bank_ar-%s.%s' \
        % (major_version, minor_version, major_version, minor_version),
    'https://github.com/gcoop-libre/trytond-analytic_account_chart_template/tarball/%s.%s#egg=trytonar_analytic_account_chart_template-%s.%s' \
        % (major_version, minor_version, major_version, minor_version),
    'git+https://github.com/reingart/pyafipws.git@py3k#egg=pyafipws-py3k'
    'git+https://github.com/pysimplesoap/pysimplesoap.git@stable_py3k#egg=pysimplesoap-stable_py3k'
    ]

setup(name=name,
    version=version,
    description='Tryton module add functionality to Cooperative Work.',
    long_description=read('README.rst'),
    author='tryton-ar',
    url='https://github.com/gcoop-libre/trytond-cooperative_ar',
    download_url=download_url,
    project_urls={
        "Bug Tracker": 'https://bugs.tryton.org/',
        "Documentation": 'https://docs.tryton.org/',
        "Forum": 'https://www.tryton.org/forum',
        "Source Code": 'https://github.com/gcoop-libre/trytond-cooperative_ar',
        },
    package_dir={'trytond.modules.cooperative_ar': '.'},
    keywords='tryton, cooperative, receipt, vacations',
    packages=(
        ['trytond.modules.cooperative_ar']
        + ['trytond.modules.cooperative_ar.%s' % p
            for p in find_packages()]
        ),
    package_data={
        'trytond.modules.cooperative_ar': (info.get('xml', [])
            + ['tryton.cfg', 'view/*.xml', 'locale/*.po', '*.fodt',
                'icons/*.svg', 'tests/*.rst', '*.txt']),
        },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Framework :: Tryton',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Legal Industry',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial :: Accounting',
        ],
    license='GPL-3',
    python_requires='>=3.5',
    install_requires=requires,
    dependency_links=dependency_links,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    cooperative_ar = trytond.modules.cooperative_ar
    """,  # noqa: E501
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    tests_require=tests_require,
    )
