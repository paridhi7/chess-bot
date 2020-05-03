import tweepy
from keys import keys

# Authenticate to Twitter
def create_api():
  CONSUMER_KEY = keys['consumer_key']
  CONSUMER_SECRET = keys['consumer_secret']
  ACCESS_TOKEN = keys['access_token']
  ACCESS_TOKEN_SECRET = keys['access_token_secret']

  auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
  auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

  api = tweepy.API(auth)

  try:
      api.verify_credentials()
      print("Authentication OK")
  except:
      print("Error during authentication")
  return api
  