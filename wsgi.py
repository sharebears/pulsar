#!/usr/bin/env python3

from pulsar import create_app

app = create_app('config.py')

if __name__ == '__main__':
    app.run()
