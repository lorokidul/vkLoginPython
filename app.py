import secrets
import requests
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__, static_url_path='/static')

app.secret_key = secrets.token_hex(16)
APP_ID = 7414616
REDIRECT_URI = 'http://127.0.0.1:5000/o/oauth2/auth'
CLIENT_SECRET = '6kMClHK2fRQXJSHM0rHr'
API_VERSION = '5.103'


@app.route('/')
def index():
    if 'user_id' in session.keys():
        return home()

    return render_template('button.html')


def get_friends_list(user_id, token):
    response = requests.get('https://api.vk.com/method/friends.get',
                             params={'access_token':token,
                                     'user_id':user_id,
                                     'fields':'city',
                                     'v':API_VERSION})
    response_json = response.json()
    return response_json["response"]


def home():
    user_id = session["user_id"]
    token = session["token"]

    friends = get_friends_list(user_id, token)
    n_friends = friends['count']
    response = requests.get('https://api.vk.com/method/photos.get', params={'owner_id': user_id,
                                           'album_id':'profile',
                                           'rev':'1',
                                           'count':'1',
                                           'access_token':token,
                                            'v':API_VERSION})

    photo_json = response.json()
    session["pic_url"] = None
    if len(photo_json['response']['items']) > 0:
        session["pic_url"] = photo_json['response']['items'][0]['sizes'][0]['url']

    session["n_friends"] = n_friends
    session["queries"] = 0

    return render_template('friends.html', pic=session["pic_url"], friends=session["n_friends"],
                           query_counter=session["queries"])



@app.route('/login_button', methods=["GET", "POST"])
def button():
    r = requests.get('https://oauth.vk.com/authorize',
                 params={'client_id':APP_ID,
                         'redirect_uri':REDIRECT_URI,
                         'scope':'friends',
                         'revoke':'1',
                         'v':API_VERSION})
    return redirect(r.url)


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

        response = requests.get('https://oauth.vk.com/access_token',
                                params={'client_id':APP_ID,
                                        'client_secret':CLIENT_SECRET,
                                        'redirect_uri':REDIRECT_URI,
                                        'code':code})

        response_json = response.json()
        token = response_json['access_token']
        user_id = response_json['user_id']

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

if __name__ == "__main__":
    app.run()
