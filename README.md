Bamboo Build Tools
==================
Python build tools for Atlassian Bamboo

Release Management in Subversion
--------------------------------
There is a set of tools used in Rutube for release management.

### SVN prerequisites
All bamboo SVN tools require SVN commit messages to start with JIRA task key,
> PROJ-123 some feature implemented.

Project directory stucture in SVN is following:
    /trunk               # trunk location
    /branches/stable     # stable branches location, named like 1.x or 1.2.x
    /tags/release        # tags location for JIRA version 1.2.3, and
    /tags/release/1.2.3/ # builds dir for version 1.2.3


Project root may be not only the repo root, but any other path, if there are several project in one SVN repo.


### svn-create-stable
Used to correctly create stable from trunk or released tag.

#### Example:
> svn-create-stable -t http://svn.example.org/project PROJ-9 1.1.x

PROJ-9 is JIRA task key for "Integration task" used in commit message for stable creation, 1.1.x - stable name.
Rules for stable creation are following:

1. Major stables are created from trunk
2. Minor stable 1.1.x is created from last build of 1.1.0 tag.

#### Other options:
* **-b** you can choose branch to copy from
* **-i** interactive mode, asks before commits
* **-c** config file (see below)
* **-t** SVN project root url

### svn-log-tasks
Used to search JIRA task keys mentioned in commit messages.

#### Example:
> svn-log-tasks -b http://svn.example.org/project PROJ

PROJ is JIRA project key. 

#### Other options:
* **-b** branch to look for tasks
* **-r** revision to start from (default is 100 revisions before HEAD)
* **-c** config file (see below)

#### Output explanation:

    collected:
    PROJ-5,PROJ-6,PROJ-8
    
    PROJ-5: 5,6,7,9,14,15
    PROJ-6: 1,2,3,4,8,10,13
    PROJ-8: 11,12
    
First line is a list of found JIRA tasks, last lines are lists of revisions sorted by JIRA tasks.

### svn-merge-tasks

Tool to collect and merge to stable all commits by JIRA task key.

#### Example:
> svn-merge-tasks -t http://svn.rutube.ru/project -i PROJ-9 PROJ-6 PROJ-5

PROJ-9 is "Integration task" used in commit message, other args are tasks to merge.

stable branch must checked out to current directory.

#### Other options:

* **-i** interactive mode, asks before commits
* **-c** config file (see below)
* **-t** SVN project root url
* **-b** branch to merge from (default is trunk)

### svn-release

Creates tag from stable

#### Example:
> svn-release -t http://svn.rutube.ru/project -i PROJ-9 1.2.3

PROJ-9 is "Integration task" used in commit message, 1.2.3 is version to build.

#### Other options:

* **-i** interactive mode, asks before commits
* **-c** config file (see below)
* **-t** SVN project root url

Script copies stable branch content to /tags/release/1.2.3/01, where 01 is incremental build number.

Stable branch is chosen automatically:
* **1.x** for major release 1.0.0
* **1.x** for minor release 1.2.0
* **1.2.x** for subminor release 1.2.3

### svn-build

Exports tags content and posts it via HTTP to WebDAV server.

#### Example:
> svn-build -t http://svn.rutube.ru/project -i project-1.2.3

match is package name prefix, 1.2.3 is version to release. Script will upload to server last tag build.

#### Other options:

* **-i** interactive mode, asks before commits
* **-c** config file (see below)
* **-t** SVN project root url

### version-stable

Computes stable name from version name

#### Example:
> version-stable -a 1.2.3

With **-a** key will list major and minor stables for this version.


Deploy and Test Tools
---------------------

### bbt-deploy
Prepares environment and deploys project to local path.

#### Example:
> bbt-deploy -d production project

"project" is project name used in paths. 
"production" is deploy type:

* **production** will deploy to /data/<project>, create virtualenv there and install packages from requires.txt
* **devel** will deploy to current directory, create virtualenv and install extra packages from requires.dev.txt
* **test**  will deploy to current directory, create virtualenv and install extra packages from requires.test.txt
* **tools** installs extra python packages used by other BBT tools.

Under the hood of this script is make command with BBT makefile bamboo/Makefile. See makefile explanation for futher info.

#### Other options:
* **-c** config file (see below)
* **-d** deploy type (explained earlier)
* **-g** use gmake (for FreeBSD)
* **-l** install virtualenv locally to `cwd`/virtualenv
* **-s** path to project source dir

### bbt-test
Runs tests and collects interesting statistics for Bamboo.

#### Example:
> bbt-test -t django project

"project" is project name used in paths.
"djando" is unittest type:

* **django** run Django unittests
* **twisted** run Twisted unittests
* **unittest** run python unittests (TBD)

#### Other options:
* **-c** config file (see below)
* **-t** unittest type (explained earlier)
* **-o** collect coverage info
* **-g** use gmake (for FreeBSD)
* **-l** usr virtualenv locally in `cwd`/virtualenv
* **-s** path to project source dir

### coverage2clover
Transforms coverage.py xml report to Atlassian Clover test report format understood by Bamboo.

#### Example:
> coverage2clover -i input.xml -o output.xml

> cat input.xml | coverage2clover > output.xml



JIRA Task Management
--------------------

### task-search

Outputs a list of tasks found by several criteries:

* **-t** task type (i.e. "Development Task")
* **-s** task status ("i.e. "Developing")
* **-u** current assignee (i.e. "username" or "currentUser()")
* **-r** release name (fixVersion, i.e. "1.2.3")

#### Example:
> task-search -u currentUser() -t "Development Ticket" -t "Development Subtask" -s "Integrating" -r "1.2.3" PROJ

"PROJ" is JIRA project key

#### Other options:
* **-c** config file (see below)

### task-versions
Output a list of unreleased and not archived versions linked to task.

#### Example:
> task-versions PROJ-6

#### Other options:
* **-c** config file (see below)

### task-assign
Assigns a task to "currentUser()" with **-m** flag or to other.

#### Example:
> task-assign -m PROJ-5

> task-assign PROJ-6 username

#### Other options:
* **-c** config file (see below)

### task-transition

Transit task over workflow

#### Example:
> task-transition PROJ-6 developed

"developed" is allowed task status name.

#### Other options:
* **-c** config file (see below)


Bamboo.cfg
----------

Python-style config file for Bamboo Build Tools.

### Example:
    # requirements filenames lists by deploy type
    requires = {
        'DEPLOY': ('requires.part1.txt', 'requires.part2.txt'),
        'DEVEL': ('requires.dev.txt'),
        'TEST': ('requires.test.txt')
    }
    
    # additional include files
    include = ('include1.mk', 'include2.mk')
    
    # additional make targets called after deploy
    extra_targets = {
        'PRODUCTION': (),
        'DEVEL': (),
        'TEST': (),
    }
    
    # JIRA credentionals
    jira_user = 'bamboo'
    jira_password = 'password'
    
    # WebDAV url for package upload
    repo_url = 'http://localhost/webdav'
    
    # JIRA project key
    project_key = 'PROJ'
    
    # SVN project root
    project_root = 'http://svn.example.org/repo/project/'
