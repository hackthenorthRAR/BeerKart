from flask import Flask, render_template, request
from flask_session import Session
from tempfile import mkdtemp
import requests
import json
import random, string

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
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (id VARCHAR PRIMARY KEY, email VARCHAR, fullname VARCHAR, photo VARCHAR, dropped INT default 0, picked INT default 0)")

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
    photo = request.form['photo']
    name = request.form['name']
    cur.execute("SELECT id, email FROM accounts WHERE id='" + id + "'")
    rows = cur.fetchall()

    for row in rows:
        if row[0] == id and row[1] == email:
            return 'signed in'

    cur.execute(
        "INSERT INTO accounts (id, email, fullname, photo) VALUES ('" + id + "', '" + email + "', '" + name + "', '" + photo + "')"
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
        "CREATE TABLE IF NOT EXISTS requests (googleid VARCHAR, id SERIAL PRIMARY KEY, pickupid VARCHAR, bottletype VARCHAR, bottlecount VARCHAR, message VARCHAR, latitude float, longitude float)"
    )

    googleId = request.form['id']
    bottleType = request.form['bottleType']
    bottleCount = request.form['bottleCount']
    comment = request.form['comment']
    lat = 0
    lon = 0
    if not 'latitude' in request.form:
        send_url = 'http://freegeoip.net/json'
        r = requests.get(send_url)
        j = json.loads(r.text)
        lat = j['latitude']
        lon = j['longitude']
    else:
        lat = request.form['latitude']
        lon = request.form['longitude']

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

    cur.execute("SELECT latitude, longitude, googleid, bottlecount, bottletype, message, id, pickupid FROM requests")

    rows = cur.fetchall()

    newRowArray = []
    for row in rows:
        newRowArray.append({
            'lat': row[0],
            'long': row[1],
            'googleid': row[2],
            'bottlecount': row[3],
            'bottletype': row[4],
            'message': row[5],
            'requestId': row[6],
            'pickupid': row[7]
        })

    for row in newRowArray:
        cur.execute("SELECT fullname, photo FROM accounts WHERE id='" + row['googleid'] + "'")
        userRow = cur.fetchone()
        row['name'] = userRow[0]
        row['photo'] = userRow[1]
        row['uniqueId'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        row['isDefaultMessage'] = row['message'] == 'Enter a message here (optional)'

    cur.close()
    return render_template("pickup.html", rows=newRowArray)

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

@app.route('/api/claimRequest', methods=['POST'])
def claimRequest():
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

    # Make each statement commit immediately.
    conn.set_session(autocommit=True)

    # Open a cursor to perform database operations.
    cur = conn.cursor()

    pickupid = request.form['googleId']
    requestId = request.form['requestId']

    cur.execute("UPDATE requests SET pickupid = '" + pickupid + "' WHERE id = " + requestId)

    cur.close()

    return 'Successful';

@app.route('/pending')
def pending():
    return render_template('pending.html')

@app.route('/pickupConfirm')
def pickupConfirm():
    return render_template('pickupConfirm.html')

@app.route('/complete')
def complete():
    return render_template('complete.html')

@app.route('/api/getAccepted', methods=['POST'])
def getAccepted():
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)
    # Make each statement commit immediately.
    conn.set_session(autocommit=True)
    # Open a cursor to perform database operations.
    cur = conn.cursor()

    cur.execute("SELECT pickupid FROM requests WHERE googleid='" + request.form['id'] + "'")
    rows = cur.fetchall()
    allSatisifed = True
    for row in rows:
        if not row[0]:
            allSatisifed = False
            break

    cur.close()

    if allSatisifed:
        return 'All taken'

    return 'Not claimed'

@app.route('/api/deleteRequest', methods=['POST'])
def delete():
    conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)
    # Make each statement commit immediately.
    conn.set_session(autocommit=True)
    # Open a cursor to perform database operations.
    cur = conn.cursor()

    cur.execute("DELETE FROM requests WHERE googleid='" + request.form['id'] + "'")

    cur.close()

    return 'Successful'

