
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from random import randint
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@35.243.220.243/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.243.220.243/proj1part2"
#
DATABASEURI = "postgresql://nd2533:5086@35.243.220.243/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  create_tweet("vladverba", "vlad's test text", "vlad's test media")
  return render_template("another.html")

@app.route('/create', methods=['GET'])
def create():
    handle = request.args.get('handle')
    text = request.args.get('text')
    media = request.args.get('media')

    handle_exists = check_if_handle_exists(handle)
    if(handle_exists):
        create_tweet(handle, text, media)

    return redirect('/')


# Checks if the user exists.
# If the user exists, display tweets of people they follow.
@app.route('/display', methods=['GET'])
def display():
    handle = request.args.get('handle')
    handle_exists = check_if_handle_exists(handle)
    if(handle_exists):
        following = get_users_someone_follows(handle)
        tweets = get_tweets_from_users(following)
        return render_template("tweets.html", tweets=tweets)
    else:
        return redirect('/')

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


# HELPER FUNCTIONS

# generates random date time for tweets (always will be in 2020)
def generate_date_time():
    month = randint(10, 12)
    day = randint(10, 28)
    year = randint(2020, 2030)

    hour = randint(00, 23)
    minute = randint(00, 59)
    second = randint(00, 59)

    return str(year) + "-" + str(month) + "-" + str(day) + " " + str(hour) + ":" + str(minute) + ":" + str(second)

# SQL QUERIES

# creates a tweet under a handle (calls on create_content)
def create_tweet(handle, text, media):
    id = randint(10000000000, 99999999999)
    while(g.conn.execute("SELECT * from tweets_with_content t where CAST(t.tid as bigint)=%s", id).fetchone() is not None):
        id = randint(10000000000, 99999999999)

    like_num = randint(0, 100000)
    retweet_num = randint(0, 100000)
    date_time = generate_date_time()

    cid = create_content(text, media)
    g.conn.execute("""INSERT INTO tweets_with_content VALUES(%s, %s, %s, %s, %s, %s)""", id, date_time, like_num, retweet_num, cid, handle)

# creates a content, returns its cid (for use in create_tweet)
def create_content(text, media):
    cid = randint(10000000000, 99999999999)
    while(g.conn.execute("SELECT * from content c where CAST(c.cid as bigint)=%s", cid).fetchone() is not None):
        cid = randint(10000000000, 99999999999)
    g.conn.execute("""INSERT INTO content VALUES (%s, %s, %s);""", cid, text, media)

    return cid


# checks if a handle exists
def check_if_handle_exists(handle):
    record = g.conn.execute("SELECT * from users u where u.handle=%s", handle).fetchone()
    if(record is None):
        return False
    else:
        return True

# returns a list of people someone follows
def get_users_someone_follows(handle):
    cursor = g.conn.execute("SELECT * from following f where f.follower=%s", handle)
    following = []
    for record in cursor:
        following.append(record['followed'])

    return following

# returns tweets that a user (a list of users) has (have) created
def get_tweets_from_users(users):
    tweets={}
    for person in users:
        cursor = g.conn.execute("SELECT * from tweets_with_content t where t.handle=%s", person)
        for record in cursor:
            media = g.conn.execute("SELECT media from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            text = g.conn.execute("SELECT text from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            tweets[record['cid']] = (text, media)

    return tweets


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
