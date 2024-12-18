import sys
from patched_imghdr import what
sys.modules['imghdr'] = sys.modules[__name__]


import tweepy

# Twitter API credentials
TWITTER_API_KEY = "HaA4FDPOUrmzhVLlKT944f7GJ"
TWITTER_API_SECRET = "9TmlCTKh3UM3W73NgjMN2r3VaL9H6xGzhdIyoMhtxQKzi8VG3A"
TWITTER_ACCESS_TOKEN = "1854656784717287439-ZsR4woWh4PWAWcHu4KfOH70XnHkyP2"
TWITTER_ACCESS_SECRET = "FuFEIQ3lY5qccNUxklpvdMzuFvUwytdWYJqPBJJiFq9pA"

# Authenticate with Twitter API
auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)

api = tweepy.API(auth)

# Test the connection
try:
    user = api.verify_credentials()
    print(f"Authenticated successfully as: {user.screen_name}")
except Exception as e:  # Updated for Tweepy v4.x+
    print(f"Failed to authenticate: {e}")


