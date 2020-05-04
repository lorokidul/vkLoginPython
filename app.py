

import json
import re
import secrets
import urllib.error
import urllib.parse
import urllib.request
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__, static_url_path='/static')

app.secret_key = secrets.token_hex(16)
APP_ID = 7414616
REDIRECT_URI = 'http://127.0.0.1:5000/o/oauth2/auth'
CLIENT_SECRET = '6kMClHK2fRQXJSHM0rHr'



@app.route('/')
def index():
    if 'user_id' in session.keys():
        return home()

    return render_template('button.html')


def get_friends_list(user_id, token):
    friends_url = get_friends_url(user_id, token)
    response = connect(friends_url)
    parsed = json.loads(response)
    return parsed["response"]


def home():
    user_id = session["user_id"]
    token = session["token"]

    friends = get_friends_list(user_id, token)
    n_friends = friends['count']

    album_url = get_album_url(user_id, "profile", 1, 1, token)
    connection = urllib.request.urlopen(album_url)
    data = connection.read().decode()

    photo_json = json.loads(data)
    session["pic_url"] = None
    if len(photo_json['response']['items']) > 0:
        user_pic_url = re.sub('//////', '//',
                              re.sub('\\\/', '///', photo_json['response']['items'][0]['sizes'][0]['url']))
        session["pic_url"] = user_pic_url

    session["n_friends"] = n_friends
    session["queries"] = 0

    return render_template('friends.html', pic=session["pic_url"], friends=session["n_friends"],
                           query_counter=session["queries"])





def get_url(client_id, redirect_uri):
    base = "https://oauth.vk.com/authorize?"
    client_id = 'client_id=' + str(client_id)
    redirect_uri = '&redirect_uri=' + str(redirect_uri)
    scope = '&scope=friends'
    version_string = "&v=5.103"
    url = base + client_id + redirect_uri + scope + version_string + "&revoke=1"
    return url


def connect(url):
    connection = urllib.request.urlopen(url)
    data = connection.read().decode()
    return data


@app.route('/login_button', methods=["GET", "POST"])
def button():
    url = get_url(APP_ID, REDIRECT_URI)
    return redirect(url)


@app.route('/logout_button', methods=["GET", "POST"])
def logout_button():
    session.clear()
    session.pop('token', None)
    session.pop('user_id', None)
    return index()


@app.route('/o/oauth2/auth')
def get_code():
    try:
        code = request.args.get('code')
        token_url = get_access_token_url(APP_ID, CLIENT_SECRET, REDIRECT_URI, code)
        response = connect(token_url)
        parsed = json.loads(response)

        token = parsed['access_token']
        user_id = parsed['user_id']

        session['user_id'] = user_id
        session['token'] = token
    except:
        session.clear()
        redirect("/")

    return redirect("/")


@app.route('/search', methods=["GET", "POST"])
def submit(name="unknown"):
    friends_info = get_friends_list(session["user_id"], session["token"])["items"]
    items = [(item["first_name"] + " " + item["last_name"]) for item in friends_info]
    session["friends"] = items
    if request.method == "POST":
        name = request.form.get("friend")
        session["friends"] = [item["first_name"] + " " + item["last_name"] for item in friends_info if
                              item["first_name"] == name]
        session["queries"] += 1

    return render_template('friends.html', pic=session["pic_url"], friends=session["n_friends"],
                           friend_list=session["friends"], friend_name=name, query_counter=session["queries"])


def get_access_token_url(client_id, client_secret, redirect_uri, code):
    base = 'https://oauth.vk.com/access_token?'
    client_id = 'client_id=' + str(client_id)
    client_secret = '&client_secret=' + str(client_secret)
    redirect_uri = '&redirect_uri=' + str(redirect_uri)
    code = '&code=' + code

    return base + client_id + client_secret + redirect_uri + code


def get_friends_url(user_id, token):
    base = 'https://api.vk.com/method/friends.get?PARAMETERS'
    token = '&access_token=' + token
    user_id = '&user_id=' + str(user_id)
    fields = '&fields=city'
    version_string = "&v=5.103"
    return base + user_id + fields + token + version_string


def get_album_url(owner_id, album_id, chronological, maxN, access_token):
    base = 'https://api.vk.com/method/photos.get?'
    owner_string = 'owner_id=' + str(owner_id)
    album_string = '&album_id=' + str(album_id)
    rev_string = '&rev=' + str(chronological)
    count_string = '&count=' + str(maxN)
    access_token_string = '&access_token=' + str(access_token)
    photo_sizes_string = "&photo_sizes=0"
    version_string = "&v=5.103"
    url = base + owner_string + album_string + rev_string + count_string + photo_sizes_string + access_token_string + version_string
    return url


if __name__ == "__main__":
    app.run()
