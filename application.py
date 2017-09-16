from flask import Flask, render_template, request
from flask_session import Session
from tempfile import mkdtemp

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

    # Insert two rows into the "accounts" table.

    #cur.execute("INSERT INTO accounts (id, email) VALUES (1, 'hello@gmail.com'), (2, 'hello2@gmail.com')")

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


#@app.route("/login")
#def login():
    #empty function

#@app.route("/pickup", methods=["GET", "POST"])
#def pickup():
    #empty function

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
