# Webapp for Spotify-Discover-2gether

This webapp is built using Python Flask and the Flask-Spotify-Auth (https://github.com/vanortg/Flask-Spotify-Auth)

## Setup

The webapp runs on localhost and port 5000.
Use the following command to run the app.

```
python3 app.py
```

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

## File Structure

 - app.py 
   - contains the flask webapp code and routes
 - startup.py
   - contains the client id, secret and the routines to perform authentication
 - flask_spotify_auth.py
   - containes the underlying authentication code

## Demo

[![Watch the Demo video](demo.gif)]
