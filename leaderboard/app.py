import os
from flask import Flask
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, Table, Column, Integer, String, create_engine

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)

debug = False

if debug:
	db = create_engine('sqlite:///testing.db')

metadata = MetaData(db)
scores = Table('scores', metadata,
	Column('id', Integer, primary_key=True),
	Column('name', String(30)),
	Column('score', Integer))
metadata.create_all()

@app.route('/')
def hello():
	return "HELLO!"

@app.route('/add/<name>/<int:score>')
def add(name, score):
	r = scores.insert().execute({'name': name, 'score': score})
	i = scores.select().where(scores.c.score < score).count().execute().scalar()

	# returns a python list literal. Use ast.literal_eval to read
	v = []
	for row in scores.select().order_by("score").offset(i-3).limit(6).execute():
		v.append("('%s', %d)" % (row['name'], row['score']))

	return "[%s]" % ', '.join(v)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug = debug)