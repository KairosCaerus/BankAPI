import flask
import sqlite3


app = flask.Flask(__name__)

x = 5

@app.route('/', methods=['GET'])
def home():
    dbconn = sqlite3.connect('testdb.db')
    cursor = dbconn.cursor()
    return "You are monkey"


app.run()
