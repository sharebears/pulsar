#!/usr/bin/env python3

"""
This script checks all usages of permissions in the codebase and compares
them to the defined permissions in module __init__ files. It will print
and error if defined permissions are unused or undefined permissions are
used. Since permissions are statically defined in the codebase, this works
great. If that ever changes in the future, this script will need modifications
made to it.
"""

import os
import re
import sys

import click

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.permissions.models import UserPermission  # noqa: F402

try:
    project_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), sys.argv[1])
except IndexError:
    click.secho(f'You must specify a dir to check.', fg='red')
    exit()

all_permissions = UserPermission.get_all_permissions()
used_permissions = []


perm_regex = re.compile(
    r"@require_permission\('([a-z_]+)'\)|assert_permission\('([a-z_]+'),|"
    r"\.has_permission\('([a-z_]+)'\)|choose_user\(.+, '([a-z_]+)'\)|"
    r"assert_user\(.+, '([a-z_]+)'\)|asrt='([a-z_]+)'|"
    r"permission='([a-z_]+)'")

for root, dirs, files in os.walk(project_dir):
    for f in files:
        if f.endswith('.py'):
            with open(os.path.join(root, f), 'r') as openfile:
                for line in openfile.readlines():
                    r = perm_regex.search(line)
                    if r:
                        for g in r.groups():
                            if g:
                                used_permissions.append(g)

unused_permissions = [a for a in set(all_permissions) if a not in used_permissions]
undefined_permissions = [u for u in set(used_permissions) if u not in all_permissions]
if unused_permissions or undefined_permissions:
    if unused_permissions:
        print('The following permissions are defined but not used: {}'.format(
            unused_permissions))
    if undefined_permissions:
        print('The following permissions are used but not defined: {}'.format(
            undefined_permissions))
    sys.exit(1)
sys.exit(0)
