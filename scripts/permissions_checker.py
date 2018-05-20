#!/usr/bin/env python3

import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pulsar.utils.permissions import get_all_permissions  # noqa

project_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pulsar')

all_permissions = get_all_permissions()
used_permissions = []


perm_regex = re.compile(
    r"@require_permission\('([a-z_]+)'\)|assert_permission\('([a-z_]+'),|"
    r"\.has_permission\('([a-z_]+)'\)|choose_user\(.+, '([a-z_]+)'\)|"
    r"asrt='([a-z_]+)'|__permission_(?:very_)?detailed__ = '([a-z_]+)'")

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

unused_permissions = [a for a in all_permissions if a not in used_permissions]
undefined_permissions = [u for u in used_permissions if u not in all_permissions]
if unused_permissions or undefined_permissions:
    if unused_permissions:
        print('The following permissions are defined but not used: {}'.format(
            unused_permissions))
    if undefined_permissions:
        print('The following permissions are used but not defined: {}'.format(
            undefined_permissions))
    sys.exit(1)
sys.exit(0)
