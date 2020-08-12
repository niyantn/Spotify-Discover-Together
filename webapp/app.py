from flask import Flask, redirect, request, json, session, jsonify
import startup
import spotipy
import uuid
import pandas as pd

app = Flask(__name__)
app.secret_key = 'the random string'
sp = ''

cache = []

# We store the User ID, and the username and write the tracks in json format to
# file "<user_id>.json"
def add_cache(user_id, username, df):
    u = uuid.uuid4().hex
    filename = F"{user_id}.json"
    matches = [ x for x in cache if x['id'] == user_id]
    df.to_json(filename, force_ascii=False)
    if len(matches) > 0 :
        return matches[0]['url']
    else:
        cache.append({ "id": user_id, "name": username, "url": u, "filename": filename })
        return u

# Lookup to see if the url exists and return the user id of your friend
def lookup_cache(url):
    try:
        user = [ x for x in cache if x['url'] == url ][0]
        return user
    except Exception as e:
        return None

def prepare_track_pd(results):
    return pd.DataFrame ({
            'artist': [ x['artists'][0]['name'] for x in results['items'] ],
            'artist_uri': [ x['artists'][0]['uri'] for x in results['items'] ],
            'song': [ x['name'] for x in results['items'] ],
            'song_uri': [ x['uri'] for x in results['items'] ],
            'duration_ms': [ x['duration_ms'] for x in results['items'] ],
            'explicit': [ x['explicit'] for x in results['items'] ],
            'album': [ x['album']['name'] for x in results['items'] ],
            'popularity': [ x['popularity'] for x in results['items'] ]
            })

# Borrowed from Arjun's Github
def create_playlist(sp, username, playlist_name, playlist_description):
    new_playlist = sp.user_playlist_create(username, playlist_name, description = playlist_description)
    return new_playlist['id']

@app.route('/')
def index():
    response = startup.getUser()
    session['state'] = 'publish'
    return redirect(response)
                                                                
@app.route('/callback/')
def callback():
    tk = startup.getUserToken(request.args['code'])
    sp = spotipy.Spotify(tk)

    # Get current logged in user's handle and top 50 tracks
    this_user = sp.current_user()
    results = sp.current_user_top_tracks(limit=50,offset=0,time_range='medium_term')
    my_top_50 = prepare_track_pd(results)

    if session['state'] == 'publish':
        # We got here from a root / route
        uurl = add_cache(this_user['id'], this_user['display_name'], my_top_50)
        print (F"Created url {uurl} for user:")
        return jsonify({ 'sharedurl': F'localhost:5000/shared/{uurl}', 'tracks': my_top_50.song.to_list() })

    else:
        # Look up friend's track list using the url
        friend = lookup_cache(session['state'])
        friends_df = None
        with open(F"{friend['filename']}", encoding='utf-8') as f:
            data = json.loads(f.read())
            friends_df = pd.DataFrame(data)
        recommended_tracks = pd.concat([friends_df, my_top_50]).song_uri.to_list()
        print ("RECOMMENDED LIST :")
        print (recommended_tracks)

        # Create the discover playlist here.
        # We read all the users playlists to make sure we do not create a duplicate one
        playlist_name = F"Spotify Discover Together ({friend['name']})"
        playlist_desc = F"Choose a friend to discover brand new music with. We create an adventurous playlist curated to both of your tastes!"
        my_playlists = sp.current_user_playlists()
        matches = [ play['id'] for play in my_playlists['items'] if play['name'] == playlist_name ]
        if len(matches):
            playlist_id = matches[0]
            print (F"Adding tracks to existing playlist {playlist_id}")
            sp.user_playlist_replace_tracks(this_user['id'], playlist_id, recommended_tracks)
        else:
            playlist_id = create_playlist(sp, 
                               this_user['id'], 
                               F"Spotify Discover Together ({friend['name']})", 
                               'Choose a friend to discover brand new music with. We create an adventurous playlist curated to both of your tastes!')
            print (F"Adding tracks to newly created playlist {playlist_id}")
            sp.user_playlist_add_tracks(this_user['id'], playlist_id, recommended_tracks, position=None)

        return redirect(F"https://open.spotify.com/playlist/{playlist_id}")

@app.route('/shared/<url>/')
def shared(url):
    session['state'] = url
    response = startup.getUser()
    return redirect(response)
    
app.run()
