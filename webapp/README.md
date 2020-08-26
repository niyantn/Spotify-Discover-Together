# Webapp for Spotify-Discover-2gether

This webapp is built using Python Flask and the Flask-Spotify-Auth module that is found @  (https://github.com/vanortg/Flask-Spotify-Auth)
This webapp uses postgressql as the backend database.

## Files

```bash
├── README.md
├── app.py
├── app.sock
├── flask_spotify_auth.py
├── newdemo.gif
├── requirements.txt
├── startup.py
└── templates
    └── test.html
```

#### flask_spotify_auth.py & startup.py
Both these files are part of the Flask-Spotify-Auth module. startup.py defines the Spotify API components such as client id, secret, callback and scopes.

#### templates
All HTML front-end templates can go into this directory and flask can serve them from there. You can move this to where the front-end developers feel comfortable

#### app.py
This is the main flask app that does all the logic. The Cluster logic has been copied into this as well.

#### app.sock
Unix socket created as a passthrough for Gunicorn. See https://medium.com/faun/deploy-flask-app-with-nginx-using-gunicorn-7fda4f50066a for more details.

## Setup

The flask app is deployed on the Google VM Instance discover-together.com. After adding your SSH key to the metadata section, you can access this server @
```
ssh discover-together.com
cd /home/Spotify-Discover-Together/webapp
```

The Flask webapp runs on localhost and port 5000.
Nginx runs on discover-together.com:80 and forwards requests to Gunicorn via a unix socket proxied to the flask app @ localhost:5000
Nginx (port 80) --> Gunicorn (app.sock) --> Flask app (port 5000)

Use the following command to run the app. Replace <username> with the username of the account signing in.
```
sudo systemctl start app
sudo chown <username>:www-data /home/Spotify-Discover-Together/webapp/app.sock
```

If the service hangs at any moment, the following can be used to restart 
```
sudo systemctl stop app
sudo systemctl start app
sudo chown <username>:www-data /home/Spotify-Discover-Together/webapp/app.sock
sudo service nginx restart
```

## Logs
Flask logs go into /var/log/discover/error.log
Nginx logs go into /var/log/nginx/error.log

## Authentication when publishing

The person that intends to share his top 50 songs can access http://localhost:5000/
This automatically redirects the user to the Spotify login page and gives back an access token at http://localhost:5000/callback
The app uses a client ID and secret that is defined in startup.py 
Since all authorization points hit the callback URL, the flask session variable is used to denote the state of this authorization as 'publish'

```
@app.route('/')
def index():
    ....
    session['state'] = 'publish'
    ....
```

## Authentication when using the shared link

The person accessing the shared link also goes through the Authentication procedure and gets redirected to the callback url at http://localhost:5000/callback
While accessing the shared link, the flask session variable stores the unique url which is used for looking up the publisher.

```
@app.route('/shared/<url>/')
def shared(url):
    session['state'] = url
    ...
```
## Callback processing

After authentication, the top 50 tracks for the logged in user are compiled into a pandas dataframe.
If the authentication is by the publisher, the dataframe is written to a json file and a unique url is generated for this user
If the authentication is by the shared user, a lookup is done to fetch the top 50 tracks from the publisher's json file. These tracks are merged with the logged in user's top 50 tracks. These tracks are then written to a newly created playlist called "Spotifty Discover Together (<friend_name>)"
The shared user is redirected to the newly created playlist automatically

## Demo

[![Watch the Demo video](newdemo.gif)]
