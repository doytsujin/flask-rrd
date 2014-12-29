from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String


db = SQLAlchemy()


class RRD(db.Model):
  """A database table for RRD databases."""

  __tablename__ = 'rrd'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(60))
  cols_n = db.Column(db.Integer)
  cols_desc = db.Column(db.String(1024))
  type = db.Column(db.String(60))
  path = db.Column(db.String(1024))

  def __repr__(self):
    return 'RRD(%r, %r, %r)' % (
      repr(self.name),
      repr(self.cols_desc.split(',')),
      repr(self.type))

  def __init__(self, name, cols, type, path):
    self.name = name
    self.cols_n = len(cols)
    self.cols_desc = ','.join(cols)
    self.type = type
    self.path = path


def make_conn_str():
  """Make an local database file on disk."""
  return 'sqlite:///flaskrrd.db'
