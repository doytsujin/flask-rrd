#!/usr/bin/env python

import json
import random
import requests
import time

from configobj import ConfigObj
from validate import Validator
from flask.ext.script import Manager
import rrdtool

from flaskrrd import app, init_webapp
from flaskrrd.model import db, RRD


manager = Manager(app)


@manager.command
def update_rrd():
  while True:
    try:
      print requests.post(
        'http://localhost:5000/update/test',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'values': [
          str(random.randint(0, 1000)),
          str(random.randint(0, 1000)),
          str(random.randint(0, 1000)),
        ]})).status_code
    except Exception:
      print 'Failed to make request, maybe server is down?'
      #raise
    finally:
      time.sleep(1)


@manager.command
def graph_rrd():
  print requests.get(
    'http://localhost:5000/graph/test').status_code

@manager.command
def create_rrd():
  print requests.post(
    'http://localhost:5000/create/test',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'metrics': ['metric1', 'metric2', 'metric3'], 'type': 'GAUGE'})).status_code


@manager.command
def dump_database():
  """Dump the flask-rrd database."""
  init_webapp()
  for r in RRD.query.all():
    print r


@manager.command
def runserver(*args, **kwargs):
  """Override default `runserver` to init webapp before running."""
  app = init_webapp()
  # TODO(sholsapp): parameterize this, but don't clobber the *args, **kwargs
  # space, because it's annoying to have to pass these in to the `run` method.
  config = ConfigObj('config/sample.config', configspec='config/sample.configspec')
  app.config_obj = config
  app.run(*args, **kwargs)


if __name__ == "__main__":
  manager.run()
