# coding: utf-8

# $Id: $
import sys


def cout(*lines):
    if not lines:
        sys.stdout.write('\n')
    for line in lines:
        sys.stdout.write(line + '\n')


def cerr(*lines):
    if not lines:
        sys.stderr.write('\n')
    for line in lines:
        sys.stderr.write(line + '\n')
