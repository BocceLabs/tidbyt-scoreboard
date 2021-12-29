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
import uuid


# Google Cloud Credentials
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/drhoffma/oddballsports_git/tidbyt-scoreboard/oddballsportstvdev-e010e1ec7ca7.json"
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
            "name": "Cleos",
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
    query_results = query.fetch()
    results = {}
    for r in query_results:
        results[r.key.id_or_name]=r
    return json.dumps(results)

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
        if "team_a_ball_color_pattern" not in data["game"]:
            data["game"]["team_a_ball_color_pattern"] = "red"
        if "team_b_ball_color_pattern" not in data["game"]:
            data["game"]["team_b_ball_color_pattern"] = "blue"
        if "time_duration" not in data["game"]:
            data["game"]["time_duration"] = str(isodate.isoduration.duration_isoformat(isodate.duration.Duration(minutes=20)))
        if "time_scheduled" not in data["game"]:
            data["game"]["time_scheduled"] = isodate.isodatetime.datetime_isoformat(
                datetime.now())

        game_id = str(uuid.uuid4())
        key = client.key("game", game_id)
        entity = datastore.Entity(key)
        entity.update({
            "game_id": game_id,
            "team_a": data["game"]["team_a"],
            "team_b": data["game"]["team_b"],
            "venue": data["game"]["venue"],
            "court": data["game"]["court"],
            "team_a_ball_color_pattern": data["game"]["team_a_ball_color_pattern"],
            "team_b_ball_color_pattern": data["game"]["team_b_ball_color_pattern"],
            "team_a_score": 0,
            "team_b_score": 0,
            "time_duration": data["game"]["time_duration"],
            "time_scheduled": data["game"]["time_scheduled"],
            "paused": False,
            "in_progress": False
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return "exception"
    return "success {}".format(game_id)

@app.route("/game/list", methods=["GET"])
def game_list():
    query = client.query(kind="game")
    results = query.fetch()
    return json.dumps(list(results))

@app.route("/game/list/<game_id>", methods=["GET"])
def game_list_by_id(game_id):
    # grab the game
    key = client.key("game", game_id)
    entity = client.get(key)
    return json.dumps(entity)

@app.route("/game/run/start/<game_id>")
def game_run_start(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        if not entity["in_progress"]:
            # calculate the end game time
            starts_at = datetime.now()
            duration = isodate.isoduration.parse_duration(entity["time_duration"])
            ends_at = starts_at + duration

            # update the game
            entity.update({
                "time_started_at": str(isodate.isodatetime.datetime_isoformat(starts_at)),
                "time_ends_at": str(isodate.isodatetime.datetime_isoformat(ends_at)),
                "in_progress": True,
                "team_a_score": 0,
                "team_b_score": 0
            })
            client.put(entity)
        else:
            raise ValueError("Game is already started")
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"


@app.route("/game/run/end/<game_id>")
def game_run_end(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        if entity["in_progress"]:
            # end game time is now
            ended_at = datetime.now()

            # update the game
            entity.update({
                "time_ended_at": str(isodate.isodatetime.datetime_isoformat(ended_at)),
                "in_progress": False
            })
            client.put(entity)
        else:
            raise ValueError("Game is already ended")
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/game/run/pause/<game_id>")
def game_run_pause(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        try:
            paused = entity["paused"]
        except KeyError:
            paused = False

        if entity["in_progress"] and not paused:
            # paused game time is now
            paused = datetime.now()

            # update the game
            entity.update({
                "time_paused": str(isodate.isodatetime.datetime_isoformat(paused)),
                "paused": True
            })
            client.put(entity)
        else:
            raise ValueError("Game is not in progress; can't be paused")
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/game/run/resume/<game_id>")
def game_run_resume(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        if entity["in_progress"] and entity["paused"]:
            old_ends_at = isodate.isodatetime.parse_datetime(entity["time_ends_at"])
            time_paused = isodate.isodatetime.parse_datetime(entity["time_paused"])
            time_resumed = datetime.now()
            try:
                cumulative_time_paused_duration = isodate.isoduration.parse_duration(entity["time_cumulative_time_paused_duration"])
            except:
                cumulative_time_paused_duration = isodate.isoduration.parse_duration(isodate.isoduration.duration_isoformat(isodate.duration.Duration(seconds=0)))
            cumulative_time_paused_duration = cumulative_time_paused_duration + (time_resumed - time_paused)
            new_ends_at = old_ends_at - cumulative_time_paused_duration

            # update the game
            entity.update({
                "time_resumed": str(isodate.isodatetime.datetime_isoformat(time_resumed)),
                "time_ends_at": str(isodate.isodatetime.datetime_isoformat(new_ends_at)),
                "time_cumulative_time_paused_duration": str(isodate.isoduration.duration_isoformat(cumulative_time_paused_duration)),
                "paused": False
            })
            client.put(entity)
        else:
            raise ValueError("Game is not in progress; can't be paused")
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/game/run/set_score/<game_id>", methods=["POST"])
def game_run_set_score(game_id):
    """
    JSON Data expected:
    {
        "team_a_score": ,
        "team_b_score": ,
    }
    """
    try:
        # grab the json data
        data = request.get_json()

        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        # ensure game is not ended
        if entity["in_progress"] and not entity["paused"]:
            # update the game
            entity.update({
                "team_a_score": data["team_a_score"],
                "team_b_score": data["team_b_score"]
            })
            client.put(entity)
        else:
            raise ValueError("Game is already ended")
    except Exception as e:
        print(str(e))
        return "exception"
    return "success"


@app.route("/tidbyt/<tidbyt_id>/set_game/<game_id>")
def game_run_set_scoreboard_display(tidbyt_id, game_id):
    try:
        # grab the tidbyt
        key = client.key("tidbyt", tidbyt_id)
        entity = client.get(key)

        # update the game
        entity.update({
            "game_id": game_id
        })
        client.put(entity)

    except Exception as e:
        print(str(e))
        return "exception"
    return "success"

@app.route("/lucky_score/<game_id>")
def lucky_score(game_id):
    mode = 'RGBA'
    size = (64, 22)
    color = (00, 00, 00)
    image = Image.new(mode, size, color)

    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        team_a_score = str(entity["team_a_score"]).zfill(2)
        team_b_score = str(entity["team_b_score"]).zfill(2)
        team_a_ball_color_pattern = entity["team_a_ball_color_pattern"]
        team_b_ball_color_pattern = entity["team_b_ball_color_pattern"]

        colors = {
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "green": (0, 135, 62),
            "pink": (255,192,203),
            "yellow": (255, 255, 0),
            "orange": (255, 128, 0),
            "black": (0, 0, 0)
        }

        # team colors
        team_a_color = colors[team_a_ball_color_pattern]
        team_b_color = colors[team_b_ball_color_pattern]

        # team box backgrounds
        size = (32, 22)
        team_a_background = Image.new(mode, size, team_a_color)
        team_b_background = Image.new(mode, size, team_b_color)

        # place the rectangles on the background
        image.paste(team_a_background, (0, 0))
        image.paste(team_b_background, (32, 0))

        # concatenate the scores
        scores_str = team_a_score + team_b_score

        for i in range(4):
            foreground = Image.open(os.path.join("luckiest_digits", scores_str[i] + ".png"))
            image.paste(foreground, (i * 16, 0), foreground)

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_str = base64.b64encode(buffered.getvalue())

        # calculate the time remaining
        if not entity["paused"] and entity["in_progress"]:
            ends_at = isodate.isodatetime.parse_datetime(entity["time_ends_at"])
            now = datetime.now()
            duration_remaining = ends_at - now
            if str(duration_remaining)[0] == "-":
                duration_remaining = "0:00:00"
            else:
                duration_remaining = str(duration_remaining)[:7]
        else:
            duration_remaining = "PAUSED"
    except:
        image = Image.open(os.path.join("oddball_graphics", "obie_red.png"))
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        image_str = base64.b64encode(buffered.getvalue())
        return json.dumps({
            "0": image_str.decode("utf-8"),
            "time_str": "0:00:00",
            "team_a": "",
            "team_b": ""
        })


    return json.dumps({
        "0": image_str.decode("utf-8"),
        "time_str": duration_remaining,
        "team_a": entity["team_a"],
        "team_b": entity["team_b"]
    })

@app.route("/setscore/<court>/<score>", methods=["GET", "POST"])
def setscore(court, score):
    s = score.split(",")
    scores[court]["score"] = score_list(s[0], s[1], s[2])
    return "success"

@app.route("/resettime/<court>", methods=["GET", "POST"])
def gettime(court):
    scores[court]["time"] = [2, 0]
    return "success"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))