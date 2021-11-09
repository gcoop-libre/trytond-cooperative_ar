#!/usr/bin/env python
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

import io
import os
import re
from configparser import ConfigParser
from setuptools import setup

MODULE = 'cooperative_ar'
PREFIX = 'trytonar'
MODULE2PREFIX = {
    'party_ar': 'trytonar',
    'bank_ar': 'trytonar',
    'analytic_account_chart_template': 'trytonar',
    'account_coop_ar': 'trytonar',
    }


def read(fname):
    return io.open(
        os.path.join(os.path.dirname(__file__), fname),
        'r', encoding='utf-8').read()


def get_require_version(name):
    #if name.startswith('trytonar_'):
        #return ''
    if name in LINKS:
        return '%s@%s' % (name, LINKS[name])
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
series = '%s.%s' % (major_version, minor_version)
if minor_version % 2:
    branch = 'master'
else:
    branch = series

download_url = 'https://github.com/gcoop-libre/trytond-cooperative_ar/tree/%s' % branch

LINKS = {
    'trytonar_party_ar': ('git+https://github.com/tryton-ar/'
        'party_ar.git@%s#egg=trytonar_party_ar-%s' %
        (branch, series)),
    'trytonar_bank_ar': ('git+https://github.com/tryton-ar/'
        'bank_ar.git@%s#egg=trytonar_bank_ar-%s' %
        (branch, series)),
    'trytonar_analytic_account_chart_template': ('git+https://github.com/gcoop-libre/'
        'trytond-analytic_account_chart_template.git@%s#egg=trytonar_analytic_account_chart_template-%s' %
        (branch, series)),
    'trytonar_account_coop_ar': ('git+https://github.com/gcoop-libre/'
        'trytond-account_coop_ar.git@%s#egg=trytonar_account_coop_ar-%s' %
        (branch, series)),
    }

requires = ['singing-girl', 'python-stdnum']
for dep in info.get('depends', []):
    if not re.match(r'(ir|res)(\W|$)', dep):
        module_name = '%s_%s' % (MODULE2PREFIX.get(dep, 'trytond'), dep)
        requires.append(get_require_version(module_name))

requires.append(get_require_version('trytond'))

tests_require = [get_require_version('proteus')]
dependency_links = list(LINKS.values())
if minor_version % 2:
    dependency_links.append('https://trydevpi.tryton.org/')

setup(name='%s_%s' % (PREFIX, MODULE),
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
    keywords='tryton, cooperative, receipt, vacations',
    package_dir={'trytond.modules.%s' % MODULE: '.'},
    packages=[
        'trytond.modules.%s' % MODULE,
        'trytond.modules.%s.tests' % MODULE,
        ],
    package_data={
        'trytond.modules.%s' % MODULE: (info.get('xml', []) + [
            'tryton.cfg', 'view/*.xml', 'locale/*.po', '*.fodt',
            '*.fods', 'icons/*.svg', '*.txt', 'tests/*.rst']),
        },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Financial :: Accounting',
        ],
    license='GPL-3',
    python_requires='>=3.6',
    install_requires=requires,
    dependency_links=dependency_links,
    zip_safe=False,
    entry_points="""
    [trytond.modules]
    %s = trytond.modules.%s
    """ % (MODULE, MODULE),
    test_suite='tests',
    test_loader='trytond.test_loader:Loader',
    tests_require=tests_require,
    )
