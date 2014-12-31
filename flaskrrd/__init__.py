import logging
import os

from flask import Flask, Response, render_template, jsonify, request, url_for
from flask.ext.bootstrap import Bootstrap
from flask.ext.restless import APIManager
import rrdtool

from flaskrrd.api import api
from flaskrrd.model import make_conn_str, db, RRD


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(RRD, methods=['GET', 'POST'])
Bootstrap(app)


def init_webapp():
  """Initialize the web application."""
  app.config['SQLALCHEMY_DATABASE_URI'] = make_conn_str()
  db.app = app
  db.init_app(app)
  db.create_all()
  return app


@app.route('/')
def index():
  return 'GOOD'


@app.route('/create/<rrd>', methods=['POST'])
def create(rrd):
  """Creates a new RRD database.

  The request should contain a JSON payload that specifies parameters to the
  `rrdtool.create` function.

  """

  desc = request.json

  log.debug('Creating database for [%s] with description [%s]', rrd, desc)

  rrd_dir = os.path.join(app.static_folder, 'rrds')
  if not os.path.exists(rrd_dir):
    os.makedirs(rrd_dir)
  rrd_path = os.path.join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))

  metrics = []
  for name in desc['metrics']:
    metrics.append(
      'DS:{name}:{type}:2000:U:U'.format(name=name, type=desc['type'])
    )

  rrdtool.create(
    rrd_path,
    '--step', '300',
    '--start', '0',
    metrics,
    'RRA:MIN:0:360:576',
    'RRA:MIN:0:30:576',
    'RRA:MIN:0:7:576',
    'RRA:AVERAGE:0:360:576',
    'RRA:AVERAGE:0:30:576',
    'RRA:AVERAGE:0:7:576',
    'RRA:AVERAGE:0:1:576',
    'RRA:MAX:0:360:576',
    'RRA:MAX:0:30:576',
    'RRA:MAX:0:7:576',)

  new_rrd = RRD(rrd, desc['metrics'], desc['type'], rrd_path)
  db.session.add(new_rrd)
  db.session.commit()

  return Response(status=200)


@app.route('/update/<rrd>', methods=['POST'])
def update(rrd):
  """Update a RRD database."""
  desc = request.json
  rrd_entry = RRD.query.filter_by(name=rrd).first()
  if not rrd_entry:
    log.error('No existing entry for rrd [%s].', rrd)
    return Response(status=405)
  rrdtool.update(str(rrd_entry.path), 'N:{data}'.format(data=':'.join(desc['values'])))
  return Response(status=200)


@app.route('/graph/<rrd>')
def graph(rrd):
  """Graph an entire RRD database.

  This functionality is a generic default that graphs all metrics contained in
  an RRD database. For customized views on an RRD database, use <fill this in
  later>.

  """

  rrd_dir = os.path.join(app.static_folder, 'rrds')
  if not os.path.exists(rrd_dir):
    os.makedirs(rrd_dir)

  rrd_path = os.path.join(rrd_dir, '{rrd}.rrd'.format(rrd=rrd))
  if not os.path.exists(rrd_path):
    log.error('The rrd [%s] does not exist!', rrd)
    return Response(status=500)

  png_path = os.path.join(rrd_dir, '{rrd}-day.png'.format(rrd=rrd))

  rrd_entry = RRD.query.filter_by(name=rrd).first()
  if not rrd_entry:
    log.error('No existing entry for rrd [%s].', rrd)
    return Response(405)

  acc = []
  for metric in rrd_entry.cols_desc.split(','):
    acc.append('DEF:{metric}_num={rrd_path}:{metric}:AVERAGE'.format(
      metric=metric,
      rrd_path=rrd_path))
    acc.append('LINE1:{metric}_num#0000FF:{metric}'.format(
      metric=metric))

  ret = rrdtool.graph(
    png_path,
    '--start', '-1d',
    '--vertical-label=Num',
    '-w 600',
    acc)
    #'GPRINT:m1_num:LAST:Last m1 value\: %2.1lf X',
    #'GPRINT:m2_num:LAST:Last m2 value\: %2.1lf X',
    #'GPRINT:m3_num:LAST:Last m3 value\: %2.1lf X',)

  return render_template('index.html', png_url=url_for('static', filename='rrds/{rrd}-day.png'.format(rrd=rrd)))
