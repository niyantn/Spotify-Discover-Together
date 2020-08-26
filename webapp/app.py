from flask import Flask, redirect, request, json, session, jsonify
import startup
import spotipy
import uuid
import pandas as pd
import logging
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import random
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQL_ENGINE = F"postgresql://discover:discover@localhost"
Base = declarative_base()
db = create_engine(F"{SQL_ENGINE}/discover")
db.connect()
db.echo = False
Session = sessionmaker(bind=db)
db_session = Session()

# Create the users table if it does not exist here.
Base.metadata.create_all(db)
app = Flask(__name__)
app.secret_key = 'the random string'
sp = ''
cache = []

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

class User(Base):
    __tablename__ = "users",
    id = Column(String, primary_key=True)
    name = Column('name', String)
    url = Column('url', String)

    @classmethod
    def find(cls, db_session, userid):
        return db_session.query(cls).filter_by(id=userid).first()

    @classmethod
    def find_by_url(cls, db_session, url):
        return db_session.query(cls).filter_by(url=url).first()


def cluster_algorithm(sp, u1_df, u2_df):
    # Copied entire logic from https://github.com/arjunrreddy/Spotify-Discover-Together/blob/master/Spotify_Data_Manipulation_For_Website.ipynb
    # return converted recommended list
    temp = pd.concat([u1_df, u2_df])
    temp.reset_index(drop=True,inplace=True)

    # Extracts each users "Top 50 Tracks" Audio features
    user1_list = []
    for song in u1_df.song_uri.to_list():
        row = pd.DataFrame(sp.audio_features(tracks=[song]))
        print(F"Adding audio features for {row}")
        user1_list.append(row)
    user1_df = pd.concat(user1_list)

    user2_list = []
    for song in u2_df.song_uri.to_list():
        row = pd.DataFrame(sp.audio_features(tracks=[song]))
        user2_list.append(row)
    user2_df = pd.concat(user2_list)

    # Combine both users' top 50 songs into one dataframe of 100 songs
    dfs = [user1_df, user2_df]
    dfs = pd.concat(dfs)
   
    # Drop unnecessary features
    dfs.drop(['type','track_href','analysis_url','time_signature','duration_ms','uri','instrumentalness','liveness','loudness','key','mode'],1,inplace=True)
    dfs.set_index('id',inplace=True) 

    # Normalize tempo feature
    columns = ['danceability','energy','speechiness','acousticness','valence','tempo']
    scaler = MinMaxScaler()
    scaler.fit(dfs[columns])
    dfs[columns] = scaler.transform(dfs[columns])

    # Get 20 clusters from 100 songs
    clusters = 20
    kmeans = KMeans(n_clusters=clusters)
    kmeans.fit(dfs)

    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(dfs)
    y_kmeans = kmeans.fit_predict(scaled)

    # Updating dataframe with assigned clusters 
    dfs['cluster'] = y_kmeans
    dfs['artist'] = temp.artist.tolist()
    dfs['title'] = temp.song.tolist()

    # Removing clusters that only have one song in them
    delete_clusters = []
    cluster = 0
    while cluster < (len(dfs.cluster.unique())-1):
        if dfs.groupby('cluster').count().loc[cluster].danceability == 1:
            delete_clusters.append(cluster)
        cluster+=1
    dfs.reset_index(inplace=True)

    i = 0
    while i < (len(dfs.cluster.unique())-1):
        if dfs.loc[[i]].cluster.tolist()[0] in delete_clusters:
            dfs.drop(i,0,inplace=True)
        i+=1
    dfs.set_index('id',inplace=True)

    #Create list of lists of song ids to put into recommendation function
    i=0
    list_of_recs = [0]*len(dfs.groupby('cluster').count())
    while i<len(dfs.groupby('cluster').count()):
        list_of_recs[i] = dfs.loc[dfs['cluster'] == i].index.to_list()
        i+=1
    list_of_recs = [ele for ele in list_of_recs if ele != []]
    print(list_of_recs)


    # Adjust list for clusters so that each cluster has a maximum of 5 seed songs
    j = 0
    adj_list_of_recs = [0]*len(list_of_recs)
    while j<len(list_of_recs):
        if 0 < len(list_of_recs[j]) < 6:
            adj_list_of_recs[j] = list_of_recs[j]
        elif len(list_of_recs[j]) > 5:
            adj_list_of_recs[j] = random.sample(list_of_recs[j], 5)
        j += 1

    #Getting 1 recommended song from each cluster with less than 4 songs, 2 recommended songs from each cluster with 4-5 songs
    k = 0
    list_of_recommendations = [0]*len(list_of_recs)
    while k < len(list_of_recs):
        if len(adj_list_of_recs[k]) < 4:
            list_of_recommendations[k] = sp.recommendations(seed_tracks=adj_list_of_recs[k],limit=1)
        else:
            list_of_recommendations[k] = sp.recommendations(seed_tracks=adj_list_of_recs[k],limit=2)
        k += 1
    pd.json_normalize(list_of_recommendations[15], record_path='tracks').id
    print (list_of_recommendations)

    list_of_recommendations_converted = [0]*len(list_of_recs)
    l = 0
    while l < len(list_of_recs):
        list_of_recommendations_converted.append(pd.json_normalize(list_of_recommendations[l], record_path='tracks').id.tolist())
        l += 1

    no_integers = [x for x in list_of_recommendations_converted if not isinstance(x, int)]
    list_of_recommendations_converted = [item for elem in no_integers for item in elem]
    return list_of_recommendations_converted


# We store the User ID, and the username and write the tracks in json format to
# file "<user_id>.json"
def add_cache(user_id, username, df):
    u = uuid.uuid4().hex
    user = User.find(db_session, user_id)
    if not user:
        db_session.add(User(id=user_id, name=username, url=u))
        db_session.commit()
        user = User.find(db_session, user_id)

    df.to_sql(username, db, if_exists="replace")
    return user.url

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
        return jsonify({ 'username': this_user['display_name'],  'sharedurl': F'http://discover-together.com/shared/{uurl}', 'tracks': my_top_50.song.to_list() })

    else:
        # Look up friend's track list using the url
        url = session['state']
        friend = User.find_by_url(db_session, url)
        if not friend:
            return jsonify({ 'error': F"The shared url http://discover-together.com/shared/{url} does not belong to any friend."}, 500)

        sql = F"select * from \"{friend.name}\""
        friends_df = pd.read_sql(sql, db)
        print(friends_df)

        try:
            recommended_tracks = cluster_algorithm(sp, my_top_50, friends_df)
            print ("RECOMMENDED LIST :")
            print (recommended_tracks)
        except Exception as e:
            return jsonify({ 'error': str(e), 'message': F"Failed to get recommended list, perhaps you dont have enough history" })

        # Create the discover playlist here.
        # We read all the users playlists to make sure we do not create a duplicate one
        playlist_name = F"Spotify Discover Together ({friend.name} & {this_user['display_name']})"
        playlist_desc = F"Choose a friend to discover brand new music with. We create an adventurous playlist curated to both of your tastes!"
        my_playlists = sp.current_user_playlists()
        matches = [ play['id'] for play in my_playlists['items'] if play['name'] == playlist_name ]
        if len(matches):
            playlist_id = matches[0]
            app.logger.info (F"Adding tracks to existing playlist {playlist_id} - {playlist_name}")
            sp.user_playlist_replace_tracks(this_user['id'], playlist_id, recommended_tracks)
        else:
            playlist_id = create_playlist(sp, this_user['id'], playlist_name, playlist_desc)
            app.logger.info (F"Adding tracks to newly created playlist {playlist_id} - {playlist_name}")
            sp.user_playlist_add_tracks(this_user['id'], playlist_id, recommended_tracks, position=None)

        return redirect(F"https://open.spotify.com/playlist/{playlist_id}")

@app.route('/shared/<url>/')
def shared(url):
    session['state'] = url
    response = startup.getUser()
    return redirect(response)

if __name__ == '__main__':
    app.run( host="0.0.0.0", debug=True )

