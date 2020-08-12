from flask_spotify_auth import getAuth, refreshAuth, getToken

#Add your client ID
CLIENT_ID = "bf16f6c8da464286ab9303ce916efffd" #"98c167e218bd483891f8638caaca19cb"

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = "a9b3001e342a4a7189b3a37016a0c36b" #"e40d06af72524208bf0bbb048ba299a3"

#Port and callback url can be changed or ledt to localhost:5000
PORT = "5000"
CALLBACK_URL = "http://localhost"

#Add needed scope from spotify user
SCOPE =  "playlist-read-private playlist-modify-private user-top-read user-read-private user-read-email playlist-modify-public" #"streaming user-read-birthdate user-read-email user-read-private"
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown 
TOKEN_DATA = []


def getUser():
    print ('getUser')
    return getAuth(CLIENT_ID, "{}:{}/callback/".format(CALLBACK_URL, PORT), SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    print ('getUserToken')
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, "{}:{}/callback/".format(CALLBACK_URL, PORT))
    return TOKEN_DATA
 
def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA
