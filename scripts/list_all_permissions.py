#!/usr/bin/env python3

from pprint import pprint

from app import create_app
from core.mixins import Permission


create_app('config.py')

pprint(list(sorted(Permission.get_all_permissions())))
