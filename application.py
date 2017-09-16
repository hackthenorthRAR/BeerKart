from flask import Flask, render_template, request
from flask_session import Session
from tempfile import mkdtemp
import requests
import json

app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# import the driver
import psycopg2

@app.route('/')
def index():
    # database link
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

    # Make each statement commit immediately.
    conn.set_session(autocommit=True)
    # Open a cursor to perform database operations.
    cur = conn.cursor()

    # Create the "accounts" table.
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (id VARCHAR PRIMARY KEY, email VARCHAR, dropped INT default 0, picked INT default 0)")

    # Print out the balances.
    cur.execute("SELECT id, email, dropped, picked FROM accounts")
    rows = cur.fetchall()
    print('Initial data:')
    for row in rows:
        print([str(cell) for cell in row])

    # Close the database connection.
    cur.close()
    conn.close()

    return render_template('index.html')

@app.route('/home')
def main():
    return render_template('home.html')

# Post Requests
@app.route('/api/signIn', methods=['POST'])
def signIn():
    # database link
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

    # Make each statement commit immediately.
    conn.set_session(autocommit=True)
    # Open a cursor to perform database operations.
    cur = conn.cursor()
    id = request.form['id']
    email = request.form['email']
    cur.execute("SELECT id, email FROM accounts WHERE id='" + id + "'")
    rows = cur.fetchall()

    for row in rows:
        if row[0] == id and row[1] == email:
            return 'signed in'

    cur.execute(
        "INSERT INTO accounts (id, email) VALUES ('" + id + "', '" + email + "')"
    )
    cur.close()
    return 'new account'

@app.route('/api/request', methods=['POST'])
def apiRequest():
    # database link
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

    # Make each statement commit immediately.
    conn.set_session(autocommit=True)

    # Open a cursor to perform database operations.
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS requests (googleid VARCHAR, id SERIAL PRIMARY KEY, bottletype VARCHAR, bottlecount VARCHAR, message VARCHAR, latitude float, longitude float)"
    )

    googleId = request.form['id']
    bottleType = request.form['bottleType']
    bottleCount = request.form['bottleCount']
    comment = request.form['comment']

    send_url = 'http://freegeoip.net/json'
    r = requests.get(send_url)
    j = json.loads(r.text)
    lat = j['latitude']
    lon = j['longitude']

    print(lat, lon)

    cur.execute(
         "INSERT INTO requests " + 
         "(googleid, bottletype, latitude, longitude, bottlecount, message)"
         + "VALUES ('" + googleId + "', '" + bottleType + "', " + str(lat) + ", " + str(lon) + ", '" + bottleCount + "', '" + comment + "')"
    )
    cur.close()
    return render_template('redirectToMain.html')

@app.route('/pickup', methods=['GET', 'POST'])
def getRequest():
    # database link
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

    # Make each statement commit immediately.
    conn.set_session(autocommit=True)

    # Open a cursor to perform database operations.
    cur = conn.cursor()

    cur.execute("SELECT latitude, longitude FROM requests")

    return render_template("pickup.html", rows=cur.fetchall())

@app.route('/makeRequest')
def requestPage():
    return render_template('makeRequest.html')

@app.route('/confirmRequest', methods=['POST'])
def confirmRequest():
    return render_template(
        'confirmRequest.html',
        bottleCount = request.form['bottleCount'],
        bottleType = request.form['bottleType'],
        comment = request.form['comment']
    )

    # TODO
    # if user click on one of the requests
    # request:id is deleted from database
    # user gets notification that their request is under way
    # show the current location and things nearby on the map
