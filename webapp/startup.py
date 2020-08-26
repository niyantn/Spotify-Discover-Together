from flask_spotify_auth import getAuth, refreshAuth, getToken

#Add your client ID
CLIENT_ID = "2e1212eddd0d4ef58ddd32576492d5ed"

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = "659d133240804da2816d45929696e1fe"

#Port and callback url can be changed or ledt to localhost:5000
CALLBACK_URL = "http://discover-together.com/callback"

#Add needed scope from spotify user
SCOPE =  "playlist-read-private playlist-modify-private user-top-read user-read-private user-read-email playlist-modify-public" #"streaming user-read-birthdate user-read-email user-read-private"
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown 
TOKEN_DATA = []


def getUser():
    print ('getUser')
    return getAuth(CLIENT_ID, CALLBACK_URL, SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    print ('getUserToken')
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)
    return TOKEN_DATA
 
def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA
