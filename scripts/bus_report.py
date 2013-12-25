# coding: utf-8

# $Id: $
from optparse import OptionParser
import sys
from bamboo.tasks import Tasks

parser = OptionParser(usage='%prog [options] <project_key>')
parser.add_option("-c", "--config-file", dest="configfile",
                  default='bamboo.cfg', help="read config from FILE",
                  metavar="FILE")
parser.add_option("-p", "--programmers", dest="programmers",
                  help='txt with programmers logins')


options, args = parser.parse_args()
if len(args) < 1:
    parser.print_usage()
    sys.exit(-1)

jira = Tasks(configfile=options.configfile)
f = open(options.programmers, 'r')
programmers = map(str.strip, f.readlines())
f.close()
counts = {}
m = 0
for p in programmers:
    query = ("project='%s'"
        " AND status WAS developed BY '%s'"
        " AND createdDate > '-180d'") % (args[0], p)
    cnt = len(jira.jira.search_issues(query, maxResults=200))
    if cnt > 0:
        counts[p] = cnt
        m = max(m, cnt)
for k in sorted(counts.keys()):
    print "%s: %0.2f (%d)" % (k, counts[k] / float(m), counts[k])
