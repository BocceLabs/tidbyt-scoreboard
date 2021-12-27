# imports
from flask import Flask
from flask import request
from flask import json
from markupsafe import escape
from PIL import Image, ImageDraw
import os
import base64
from io import BytesIO
from google.cloud import datastore
from google.oauth2 import service_account
from google.cloud import language
from datetime import datetime
import isodate


# Google Cloud Credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/drhoffma/oddballsports_git/tidbyt-scoreboard/oddballsportstvdev-e010e1ec7ca7.json"
# credentials = service_account.Credentials.from_service_account_file(os.path.join(".", "oddballsportstvdev-e010e1ec7ca7.json"))
# client = language.LanguageServiceClient(credentials=credentials)
client = datastore.Client(
    project="oddballsportstvdev"
)

# Flask App
app = Flask(__name__)

def score_list(a, b, poss):
    return [str(a).zfill(2), str(b).zfill(2), int(poss)]

scores = {
    "A": {
        "score": score_list(0, 0, 0),
        "time": [20, 00]
    }

}

@app.route("/venue/list", methods=["GET"])
def venue_list():
    query = client.query(kind="venue")
    results = query.fetch()
    return json.dumps(list(results))

@app.route("/venue/add", methods=["POST"])
def venue_add():
    """
    JSON Data expected:
    {
        "venue": {
            "name": "Tuman's Tap Room",
            "city": "Chicago"
        }
    }
    """
    try:
        data = request.get_json()
        venue_key = client.key("venue", data["venue"]["name"])
        court_key = client.key("court", parent=venue_key)
        entity = datastore.Entity(venue_key)
        entity.update({
            "name": data["venue"]["name"],
            "city": data["venue"]["city"]
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/court/list", methods=["GET"])
def court_list():
    # query for venues
    venue_query = client.query(kind="venue")
    venue_results = venue_query.fetch()
    venue_ids = [r.key.id_or_name for r in venue_results]

    # query for courts asscoiated with venues and build dictionary
    results = {}
    for venue_id in venue_ids:
        query = client.query(kind="court", ancestor=client.key("venue", venue_id))
        court_results = query.fetch()
        results[venue_id] = []
        for court in court_results:
            results[venue_id].append(court)

    return json.dumps(results)

@app.route("/court/list/<venue>", methods=["GET"])
def court_list_per_venue(venue):
    query = client.query(kind="court", ancestor=client.key("venue", venue))
    results = query.fetch()
    return json.dumps(list(results))

@app.route("/court/add", methods=["POST"])
def court_add():
    """
    JSON Data expected:
    {
        "venue": {
            "name": "Cleo's",
            "court": {
                "name": "Left",
                "dimensions": "30x8"
            }
        }
    }
    """
    try:
        data = request.get_json()
        parent_key = client.key("venue", data["venue"]["name"])
        key = client.key("court", data["venue"]["court"]["name"], parent=parent_key)
        entity = datastore.Entity(key)
        entity.update({
            "name": data["venue"]["court"]["name"],
            "dimensions": data["venue"]["court"]["dimensions"],
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/tidbyt/list", methods=["GET"])
def tidbyt_list():
    query = client.query(kind="tidbyt")
    results = query.fetch()
    return json.dumps(list(results))

@app.route("/tidbyt/add", methods=["POST"])
def tidbyt_add():
    """
    JSON Data expected:
    {
        "tidbyt": {
            "name": "abc-0000",
            "device_id": "insert-device-id",
            "api_key": "insert-api-key"
        }
    }
    """
    try:
        data = request.get_json()
        key = client.key("tidbyt", data["tidbyt"]["name"])
        entity = datastore.Entity(key)
        entity.update({
            "name": data["tidbyt"]["name"],
            "device_id": data["tidbyt"]["device_id"],
            "api_key": data["tidbyt"]["api_key"]
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return "exception: {}".format(str(e))
    return "success"

@app.route("/game/add", methods=["POST"])
def game_add():
    """
    JSON Data expected:
    {
        "game": {
            "team_a": "Daddy's",
            "team_b": "Rats",
            "venue": "Cleo's", | optional
            "court": "Fence", | optional
            "datetime": isodate.isodatetime.datetime_isoformat(datetime.now()), | optional
            "team_a_ball_color_pattern": "yellow", | optional
            "team_b_ball_color_pattern": "pink" | optional
        }

    }
    """
    try:
        data = request.get_json()

        if "venue" not in data["game"]:
            data["game"]["venue"] = "unassigned"
        if "court" not in data["game"]:
            data["game"]["court"] = "unassigned"
        if "datetime" not in data["game"]:
            data["game"]["datetime"] = isodate.isodatetime.datetime_isoformat(datetime.now())
        if "team_a_ball_color_pattern" not in data["game"]:
            data["game"]["team_a_ball_color_pattern"] = "red"
        if "team_b_ball_color_pattern" not in data["game"]:
            data["game"]["team_b_ball_color_pattern"] = "blue"


        key = client.key("game")
        entity = datastore.Entity(key)
        entity.update({
            "team_a": data["game"]["team_a"],
            "team_b": data["game"]["team_b"],
            "venue": data["game"]["venue"],
            "court": data["game"]["court"],
            "datetime": data["game"]["datetime"],
            "team_a_ball_color_pattern": data["game"]["team_a_ball_color_pattern"],
            "team_b_ball_color_pattern": data["game"]["team_b_ball_color_pattern"]
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/game/list", methods=["GET"])
def game_list():
    query = client.query(kind="game")
    results = query.fetch()
    return json.dumps(list(results))



##### Everything below here is old junk



@app.route("/score/<court>")
def score(court):
    # grab the time and calculate the new time
    MM, SS = scores[court]["time"]

    # convert to integer
    MM = int(MM)
    SS = int(SS)

    # subtract a second
    SS -= 1

    # if seconds are negative, update minutes
    if SS < 0:
        # if minutes are greater or equal to 1, reset the seconds and
        # subtract a minute
        if MM >= 1:
            SS = 59
            MM -= 1

        # otherwise there is no time left
        else:
            SS = 0
            MM = 0


    scores[court]["time"] = [str(MM).zfill(2), str(SS).zfill(2)]
    return json.dumps(scores)

@app.route("/lucky_score/<court>")
def lucky_score(court):
    mode = 'RGBA'
    size = (64, 22)
    color = (00, 00, 00)
    image = Image.new(mode, size, color)

    # team colors
    team_a_color = (255, 0, 0)
    team_b_color = (0, 135, 62)

    # team box backgrounds
    size = (32, 22)
    team_a_background = Image.new(mode, size, team_a_color)
    team_b_background = Image.new(mode, size, team_b_color)

    # place the rectangles on the background
    image.paste(team_a_background, (0, 0))
    image.paste(team_b_background, (32, 0))

    # extract the score
    score_team_a = scores[court]["score"][0]
    score_team_b = scores[court]["score"][1]

    # concatenate the scores
    scores_str = score_team_a + score_team_b

    for i in range(4):
        foreground = Image.open(os.path.join("luckiest_digits", scores_str[i] + ".png"))
        image.paste(foreground, (i * 16, 0), foreground)


    buffered = BytesIO()
    image.save(buffered, format="PNG")
    image_str = base64.b64encode(buffered.getvalue())

    return json.dumps({"0": image_str.decode("utf-8")})

@app.route("/setscore/<court>/<score>", methods=["GET", "POST"])
def setscore(court, score):
    s = score.split(",")
    scores[court]["score"] = score_list(s[0], s[1], s[2])
    return "success"

@app.route("/resettime/<court>", methods=["GET", "POST"])
def gettime(court):
    scores[court]["time"] = [2, 0]
    return "success"