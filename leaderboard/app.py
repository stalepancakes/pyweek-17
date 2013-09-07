import os
from flask import Flask

app = Flask(__name__)

c = 1

@app.route('/')
def hello():
	global c
	c += 1
	x = 'Hello %s' % c
	return x

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)