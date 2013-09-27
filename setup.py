from distutils.core import setup

setup(
    name='bamboo-build-tools',
    version='1.1.0',
    packages=['bamboo'],
    url='http://rutube.ru',
    license='Beer Licence',
    author='tumbler',
    author_email='stikhonov@rutube.ru',
    scripts=[
        'bin/bbt-deploy',
        'bin/bbt-test',
        'bin/build-comment',
        'bin/coverage2clover',
        'bin/svn-log-tasks',
        'bin/svn-create-stable',
        'bin/svn-merge-tasks',
        'bin/svn-release',
        'bin/svn-build',
        'bin/task-search',
        'bin/task-versions',
        'bin/task-assign',
        'bin/task-info',
        'bin/task-transition',
        'bin/version-stable'
    ],
    package_data={'bamboo': ['Makefile']},
    description='python build tools for Atlassian Bamboo',
    install_requires=[
        'lxml',
        'jira-python'
    ],
)
