from flask import Flask, render_template, url_for, request, redirect, jsonify
from flask import session as login_session, make_response, flash
import random
import string
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:catalog@localhost:2222/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# home page


@app.route('/')
@app.route('/items/')
def show_home():
    category = session.query(Category)
    return render_template('index.html', category=category)

# items in a category


@app.route('/items/<string:category_name>/<int:category_id>')
def show_items(category_name, category_id):
    category = session.query(Category)
    items = session.query(Item).filter_by(category_id=category_id)
    return render_template('items.html', category=category, items=items)

# show single item


@app.route('/items/<int:item_id>')
def show_item(item_id):
    item = session.query(Item).filter_by(id=item_id)
    return render_template('item.html', item=item)

# add new item


@app.route('/items/new', methods=['POST', 'GET'])
def add_item():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            category_id=request.form['category'],
            description=request.form['description'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('add_item.html')

# edit item


@app.route('/items/<int:item_id>/edit', methods=['POST', 'GET'])
def edit_item(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(id=item_id).one()
    category = session.query(Category).filter_by(id=item.category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            item.category_id = request.form['category']
        return redirect(url_for('show_home'))
    else:
        return render_template('edit_item.html', item=item, category=category)

# delete item


@app.route('/items/<int:item_id>/delete', methods=['POST', 'GET'])
def delete_item(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('show_home'))
    else:
        return render_template('delete_item.html', item=item)

# json endpoint


@app.route('/items/<int:item_id>/JSON')
def itemJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# login


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px; '
    '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# logout


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?'
    'token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully Logged Out.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps(
                'Failed to revoke token for given user.',
                400))
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run()
