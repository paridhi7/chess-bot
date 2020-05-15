import tweepy
import chess
import chess.svg
import json
import os

from cairosvg import svg2png
from config import create_api

GAME_TWEETS_LIST = []
GAME_REPLIES_DICT = {} # dictionary with keys as individual games; values as lists of all replies to that game from least recent to most recent
GAME_BOARD_DICT = {} # dictionary with keys as individual games; values as FEN representation of the latest chess board
GAME_PLAYER = {}  # dictionary of dictionary with outer keys as individual games; values as dictionary storing player's Twitter handles


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
      GAME_PLAYER[int(tweet.id)] = {0: None, 1: None}
      #print(tweet.id, GAME_TWEETS_LIST, GAME_REPLIES_DICT)
      print(f"{tweet.user.name} said {tweet.text}")
      sn = tweet.user.screen_name
      m = "Hello! Let's play chess. Here's the board: \n"
      board = create_chess_board(int(tweet.id))
      s = print_board(api, tweet, board, m)
      GAME_REPLIES_DICT[int(tweet.id)].append(s.id)


def update_board(game, move):
  """
  Makes a move on the board and updates it if the move is legal according to chess rules.
  """
  try:
    board = chess.Board(GAME_BOARD_DICT[game])
    board.push_san(move)
    GAME_BOARD_DICT[game] = board.fen()
    
    print(str(board))

    # check for mates
  except ValueError:
    popped = GAME_REPLIES_DICT[game].pop()
    print("Invalid move" + str(popped))


def check_results(game):
  """
  Checks the results of the game and returns the appropriate message.
  """
  board = chess.Board(GAME_BOARD_DICT[game])

  if board.is_checkmate():
    msg = "CHECKMATE: " + GAME_PLAYER[game][int(not board.turn)] + " WINS!"
  elif board.is_check():
    msg = "CHECK"
  elif board.is_stalemate():
    msg = "draw: stalemate"
  elif board.is_fivefold_repetition():
    msg = "draw: 5-fold repetition"
  elif board.is_insufficient_material():
    msg = "draw: insufficient material"
  elif board.can_claim_draw():
    msg = "draw: claim"
  else:
    msg = ""
  return msg + "\n"


def parse_latest_replies(api):
  """
  Parses the games' tweet threads to get the latest move. Checks validity of each move. Prints the updated board.
  """

  get_latest_replies(api)
  for game in GAME_REPLIES_DICT:
    if len(GAME_REPLIES_DICT[game]) > 1:
      if is_valid_turn(game, api):
        latest_reply = api.get_status(GAME_REPLIES_DICT[game][-1]).text.split()[-1]
        update_board(game, latest_reply)
        result = check_results(game)
        print_board(api=api, 
                         tweet=api.get_status(int(GAME_REPLIES_DICT[game][-1])),
                         board=chess.Board(GAME_BOARD_DICT[game]),
                         optional_msg=result)
      else:
        GAME_REPLIES_DICT[game].pop()


def is_valid_turn(game, api):
  """
  Checks if the player is not playing out of turn

  Returns True if the move is valid; False otherwise
  """
  latest_reply_uname = api.get_status(int(GAME_REPLIES_DICT[game][-1])).user.screen_name
  
  #parses the string representation of the chess board
  board = chess.Board(GAME_BOARD_DICT[game])
  
  if not GAME_PLAYER[game][int(board.turn)] == latest_reply_uname:
    return False

  return True


def get_latest_replies(api):
  """
  Stores the latest tweets for each ongoing game and sets games' players
  """
  timeline = api.mentions_timeline()
  for tweet in timeline:
    if hasattr(tweet, 'in_reply_to_status_id_str') and tweet.in_reply_to_status_id_str: #if the tweet is a reply
      parent_tweet = int(tweet.in_reply_to_status_id_str)
      grandparent_tweet = int(api.get_status(parent_tweet).in_reply_to_status_id_str)
      for game in GAME_REPLIES_DICT:
        if grandparent_tweet == game:
          if tweet.id not in GAME_REPLIES_DICT[game]:
            GAME_REPLIES_DICT[game].append(tweet.id)
            GAME_PLAYER[game][1] = tweet.user.screen_name
        elif grandparent_tweet == GAME_REPLIES_DICT[game][-1]:
          if tweet.id not in GAME_REPLIES_DICT[game]:
            GAME_REPLIES_DICT[game].extend([parent_tweet, tweet.id])
            if not GAME_PLAYER[game][0]:
              GAME_PLAYER[game][0] = tweet.user.screen_name
              

def print_board(api, tweet, board, optional_msg="", text_only=False):
  """
  Prints the current status of the chess board in text format in a new reply

  :param api: API object
  :param tweet: Status object for the tweet to reply to
  :param board: chess.Board object
  :param optional_msg: optional message to be printed with the board
  """
  sn = tweet.user.screen_name
  msg = "@%s " % (sn)
  optional_msg = msg + optional_msg + "\n"
  message = optional_msg
  if text_only:
    message += str(board)
  message += '\n\n'+"Play the next move (Capital=White)..."

  if text_only:
    try:
      s = api.update_status(message, tweet.id)
      return s
    except tweepy.error.TweepError:
      print("Already replied to this tweet")
  else:
    img = get_board_png(board)
    try:
      s = api.update_with_media(filename=img, 
        status=message,
        in_reply_to_status_id=tweet.id)
      return s
    except tweepy.error.TweepError:
      print("Already replied to this tweet")
    os.remove(img)


def get_board_png(board):
  """
  Generates a png file from the board and returns the png filename

  :param board: chess.Board object
  :return: String containing the png filename
  """
  svg_xml = chess.svg.board(board=board)
  png_filename = "board.png"
  svg2png(bytestring=svg_xml, write_to=png_filename)

  return png_filename


def create_chess_board(game):
  """
  Initialises a new chess board for the game

  :param game: Tweet id of the starter tweet for the game
  """
  board = chess.Board()
  #SVG(chess.svg.board(board=board,size=400))
  GAME_BOARD_DICT[game] = board.fen()
  return board


def main():
  global GAME_REPLIES_DICT, GAME_TWEETS_LIST, GAME_BOARD_DICT, GAME_PLAYER
  
  try:
    with open('GAME_REPLIES_DICT.json') as f:
      GAME_REPLIES_DICT = json.load(f)
    with open('GAME_TWEETS_LIST.json') as f:
      GAME_TWEETS_LIST = json.load(f)
    with open('GAME_BOARD_DICT.json') as f:
      GAME_BOARD_DICT = json.load(f)
    with open('GAME_PLAYER.json') as f:
      GAME_PLAYER = json.load(f)
  except:
    None

  GAME_REPLIES_DICT = {int(k):v for k,v in GAME_REPLIES_DICT.items()}
  GAME_BOARD_DICT = {int(k):v for k,v in GAME_BOARD_DICT.items()}
  GAME_PLAYER = {int(k):v for k,v in GAME_PLAYER.items()}
  for player in GAME_PLAYER:
    GAME_PLAYER[player] = {int(k):v for k,v in GAME_PLAYER[player].items()}

  
  api = create_api()
  invite_new_players(api)
  parse_latest_replies(api)

  with open('GAME_REPLIES_DICT.json', 'w') as f:
    json.dump(GAME_REPLIES_DICT, f)
  with open('GAME_TWEETS_LIST.json', 'w') as f:
    json.dump(GAME_TWEETS_LIST, f)
  with open('GAME_BOARD_DICT.json', 'w') as f:
    json.dump(GAME_BOARD_DICT, f)
  with open('GAME_PLAYER.json', 'w') as f:
    json.dump(GAME_PLAYER, f)
    

if __name__=="__main__":
  main()
  #create_chess_board()

