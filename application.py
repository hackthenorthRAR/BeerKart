from flask import Flask, render_template
app = Flask(__name__)
# import the driver
import psycopg2

# database link
conn = psycopg2.connect(database='users', user='maxroach', host='localhost', port=26257)

# Make each statement commit immediately.
conn.set_session(autocommit=True)

# Open a cursor to perform database operations.
cur = conn.cursor()

@app.route('/')
def index():

    # Create the "accounts" table.
    cur.execute("CREATE TABLE IF NOT EXISTS accounts (id INT PRIMARY KEY, email VARCHAR)")

    # Insert two rows into the "accounts" table.
    cur.execute("INSERT INTO accounts (id, email) VALUES (1, 'hello@gmail.com'), (2, 'hello2@gmail.com')")

    # Print out the balances.
    cur.execute("SELECT id, email FROM accounts")
    rows = cur.fetchall()
    print('Initial data:')
    for row in rows:
        print([str(cell) for cell in row])

    # Close the database connection.
    cur.close()
    conn.close()

    return render_template('index.html')
