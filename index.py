import tweepy
import chess
import chess.svg
from config import create_api
import json

GAME_TWEETS_LIST = []
GAME_REPLIES_DICT = {} # dictionary with keys as individual games whose values are lists of all replies to that game from least recent to most recent

#{"123232354950976": ["13235032909", "391039239231111", "3121233239999", "868769806"],
# "134433434343435": ["19039344344", "429222122111111"]}

def invite_new_players(api):
  """
  Checks for new mentions of the chessbot's Twitter handle. Invites them to play by printing the initial position of the board.
  """
  timeline = api.mentions_timeline()
  len_timeline = len(timeline)
  for tweet in timeline:
    if tweet.id not in GAME_TWEETS_LIST and not tweet.in_reply_to_status_id_str:
      GAME_TWEETS_LIST.append(tweet.id)
      GAME_REPLIES_DICT[int(tweet.id)] = []
      print(tweet.id, GAME_TWEETS_LIST, GAME_REPLIES_DICT)
      print(f"{tweet.user.name} said {tweet.text}")
      sn = tweet.user.screen_name
      m = "@%s Hello! Let's play chess. Here's the board: \n" % (sn)
      board = create_chess_board()
      s = print_board_text(api, tweet, sn, board, m)
      GAME_REPLIES_DICT[int(tweet.id)].append(s.id)


def parse_latest_replies(api):
  """
  Parses the games' tweet threads to get the latest move. Checks validity of each move. Prints the updated board.
  """
  get_latest_replies(api)
  latest_reply = api.get_status()


def get_latest_replies(api):
  """
  Stores the latest tweets for each ongoing game
  """
  timeline = api.mentions_timeline()
  for tweet in timeline:
    if hasattr(tweet, 'in_reply_to_status_id_str') and tweet.in_reply_to_status_id_str: #if the tweet is a reply
      parent_tweet = int(tweet.in_reply_to_status_id_str)
      grandparent_tweet = int(api.get_status(parent_tweet).in_reply_to_status_id_str)
      for game in GAME_REPLIES_DICT:
        if grandparent_tweet == game:
          GAME_REPLIES_DICT[game].append(tweet.id)
        elif grandparent_tweet == GAME_REPLIES_DICT[game][-1]:
          GAME_REPLIES_DICT[game].extend([parent_tweet, tweet.id])
  print(GAME_REPLIES_DICT)


def print_board_text(api, tweet, sn, board, optional_msg=None):
  """
  Prints the current status of the chess board in text format in a new reply

  :param api: API object
  :param tweet: Status object for the tweet to reply to
  :param sn: screen name
  :param board: chess.Board object
  :param optional_msg: optional message to be printed with the board
  """
  message = str(board)+'\n\n'+"Play the next move..."
  if optional_msg:
    message = optional_msg + "\n" + message
  try:
    s = api.update_status(message, tweet.id)
    return s
  except tweepy.error.TweepError:
    print("Already replied to this tweet")

def create_chess_board():
  """
  Initialises a new chess board
  """
  board = chess.Board()
  #SVG(chess.svg.board(board=board,size=400))
  return board


def main():
  global GAME_REPLIES_DICT, GAME_TWEETS_LIST
  try:
    with open('GAME_REPLIES_DICT.json') as f:
      GAME_REPLIES_DICT = json.load(f)
    with open('GAME_TWEETS_LIST.json') as f:
      GAME_TWEETS_LIST = json.load(f)
  except:
    None

  GAME_REPLIES_DICT = {int(k):v for k,v in GAME_REPLIES_DICT.items()}

  api = create_api()
  invite_new_players(api)
  parse_latest_replies(api)

  with open('GAME_REPLIES_DICT.json', 'w') as f:
    json.dump(GAME_REPLIES_DICT, f)
  with open('GAME_TWEETS_LIST.json', 'w') as f:
    json.dump(GAME_TWEETS_LIST, f)
    

if __name__=="__main__":
  main()
  #create_chess_board()






"""
class Tweet:
  text = ""
  username = ""
  time = ""

  in_reply_to_status_id_str = None #id of parent tweet

  def _check_if_parent_exists_and_update_its_id()
  if original exists:
    in_reply_to_status_id_str = original.id
"""