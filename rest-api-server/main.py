# imports
from flask import Flask
from flask import request
from flask import abort
from functools import wraps
from flask import json
from flask import jsonify
from flask_cors import CORS
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
# NOTE: enable this environment variable for local testing and disable it before deployment
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/drhoffma/oddballsports_git/tidbyt-scoreboard/oddballsportstvdev-e010e1ec7ca7.json"
client = datastore.Client(
    project="oddballsportstvdev"
)

# Flask App
app = Flask(__name__)
CORS(app)

# decorator which ensures a valid API key is passed in the headers
def require_appkey(view_function):
    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        # grab the authorization header
        headers = request.headers
        auth = headers.get("X-Api-Key")

        # query for api keys
        apikey_query = client.query(kind="api_key")
        apikeys = apikey_query.fetch()
        apikeys = {r.key.id_or_name: r for r in apikeys}

        if auth not in apikeys:
            abort(401)
        else:
            return view_function(*args, **kwargs)
    return decorated_function

@app.route("/venue/list", methods=["GET"])
@require_appkey
def venue_list():
    try:
        venue_query = client.query(kind="venue")
        venue_results = venue_query.fetch()
        venues = {r.key.id_or_name: r for r in venue_results}
        results = {
            "status": "success",
            "venues": venues
        }
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps(results)

@app.route("/venue/add", methods=["POST"])
@require_appkey
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
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/court/list", methods=["GET"])
@require_appkey
def court_list():
    try:
        # query for venues
        venue_query = client.query(kind="venue")
        venue_results = venue_query.fetch()
        venue_ids = [r.key.id_or_name for r in venue_results]

        # query for courts asscoiated with venues and build dictionary
        courts = {}
        for venue_id in venue_ids:
            query = client.query(kind="court", ancestor=client.key("venue", venue_id))
            court_results = query.fetch()
            courts[venue_id] = []
            for court in court_results:
                courts[venue_id].append(court)

        results = {
            "status": "success",
            "courts": courts
        }
    except Exception as e:
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps(results)

@app.route("/court/list/<venue>", methods=["GET"])
@require_appkey
def court_list_per_venue(venue):
    try:
        query = client.query(kind="court", ancestor=client.key("venue", venue))
        courts = query.fetch()
        results = {
            "status": "success",
            "courts": {
                venue: list(courts)
            }
        }
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })

    return json.dumps(results)

@app.route("/court/add", methods=["POST"])
@require_appkey
def court_add():
    """
    JSON Data expected:
    {
        "venue": {
            "name": "Cleos",
            "court": {
                "name": "Patio",
                "dimensions": "30x8",
                "ends": ["Alley", "Tables"]
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
            "ends": data["venue"]["court"]["ends"]
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/tidbyt/list", methods=["GET"])
@require_appkey
def tidbyt_list():
    try:
        query = client.query(kind="tidbyt")
        tidbyts = query.fetch()
        tidbyts = {r.key.id_or_name: r for r in tidbyts}
        results = {
            "status": "success",
            "tidbyts": tidbyts
        }
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps(results)

@app.route("/tidbyt/add", methods=["POST"])
@require_appkey
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
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/game/add", methods=["POST"])
@require_appkey
def game_add():
    """
    JSON Data expected:
    {
        "game": {
            "team_a": "Daddy's",
            "team_b": "Rats",
            "venue": "Cleo's", | optional
            "court": "Fence", | optional
            "time_scheduled": isodate.isodatetime.datetime_isoformat(datetime.now()),
            "team_a_ball_color_pattern": "yellow", | optional
            "team_b_ball_color_pattern": "pink" | optional
            "throwing_pairs": {
				"team_a": {
					"Alley": [
						"David Hoffman",
						"Jamie Lescher"
					],
					"Tables": [
						"Elizabeth Hoffman",
						"Chris Todaro"
					]
				},
				"team_b": {
					"Alley": [
						"Alex Gara",
						"Nick"
					],
					"Tables": [
						"Scott Sansbury",
						"Lydia Gara"
					]
				}
			},
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
        if "timer_duration" not in data["game"]:
            data["game"]["timer_duration"] = str(isodate.isoduration.duration_isoformat(isodate.duration.Duration(minutes=20)))
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
            "timer_duration": data["game"]["timer_duration"],
            "time_scheduled": data["game"]["time_scheduled"],
            "paused": False,
            "in_progress": False,
            "throwing_pairs": data["game"]["throwing_pairs"],
            "frames": []
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return "success {}".format(game_id)

@app.route("/game/list", methods=["GET"])
@require_appkey
def game_list():
    try:
        query = client.query(kind="game")
        games = query.fetch()
        games = {r.key.id_or_name: r for r in games}
        results = {
            "status": "success",
            "games": games
        }
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })

    return json.dumps(results)

@app.route("/game/list/<game_id>", methods=["GET"])
@require_appkey
def game_list_by_id(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)
        results = {
            "status": "success",
            "games": {
                game_id: entity
            }
        }
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps(results)

@app.route("/game/run/start/<game_id>")
@require_appkey
def game_run_start(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        if not entity["in_progress"]:
            # calculate the end game time
            starts_at = datetime.now()
            duration = isodate.isoduration.parse_duration(entity["timer_duration"])
            ends_at = starts_at + duration

            # update the game
            entity.update({
                "time_started_at": str(isodate.isodatetime.datetime_isoformat(starts_at)),
                "timer_ends_at": str(isodate.isodatetime.datetime_isoformat(ends_at)),
                "in_progress": True
            })
            client.put(entity)
        else:
            raise ValueError("Game is already started")
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })


@app.route("/game/run/end/<game_id>")
@require_appkey
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
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/game/run/pause/<game_id>")
@require_appkey
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
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/game/run/resume/<game_id>")
@require_appkey
def game_run_resume(game_id):
    try:
        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        if entity["in_progress"] and entity["paused"]:
            old_ends_at = isodate.isodatetime.parse_datetime(entity["timer_ends_at"])
            time_paused = isodate.isodatetime.parse_datetime(entity["time_paused"])
            time_resumed = datetime.now()
            try:
                cumulative_time_paused_duration = isodate.isoduration.parse_duration(entity["time_cumulative_time_paused_duration"])
            except:
                cumulative_time_paused_duration = isodate.isoduration.parse_duration(isodate.isoduration.duration_isoformat(isodate.duration.Duration(seconds=0)))
            cumulative_time_paused_duration = cumulative_time_paused_duration + (time_resumed - time_paused)
            new_ends_at = old_ends_at + (time_resumed - time_paused)

            # update the game
            entity.update({
                "time_resumed": str(isodate.isodatetime.datetime_isoformat(time_resumed)),
                "timer_ends_at": str(isodate.isodatetime.datetime_isoformat(new_ends_at)),
                "time_cumulative_time_paused_duration": str(isodate.isoduration.duration_isoformat(cumulative_time_paused_duration)),
                "paused": False
            })
            client.put(entity)
        else:
            raise ValueError("Game is not in progress; can't be paused")
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/game/run/set_score/<game_id>", methods=["POST"])
@require_appkey
def game_run_set_score(game_id):
    """
    JSON Data expected:
    {
        "team_a_score": 4,
        "team_b_score": 3,
        "append_frame": {
            "side": "Alley",
            "pallino_control": "team_b",
            "team_a_points": 0,
            "team_b_points": 2
        }
    }
    """
    try:
        # grab the json data
        data = request.get_json()

        # grab the game
        key = client.key("game", game_id)
        entity = client.get(key)

        # grab and append the frames
        frames = entity["frames"]
        frames.append(data["append_frame"])

        # ensure game is not ended
        if entity["in_progress"] and not entity["paused"]:
            # update the game
            entity.update({
                "team_a_score": data["team_a_score"],
                "team_b_score": data["team_b_score"],
                "frames": frames
            })
            client.put(entity)
        else:
            raise ValueError("Game is already ended")
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })


@app.route("/tidbyt/<tidbyt_id>/set_game/<game_id>")
@require_appkey
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
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })

@app.route("/lucky_score/<game_id>")
@require_appkey
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
            ends_at = isodate.isodatetime.parse_datetime(entity["timer_ends_at"])
            now = datetime.now()
            duration_remaining = ends_at - now
            if str(duration_remaining)[0] == "-":
                duration_remaining = "0:00:00"
            else:
                duration_remaining = str(duration_remaining)[:7]
        elif not entity["paused"] and not entity["in_progress"]:
            duration_remaining = "NOT STARTED"
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

@app.route("/user/add/<google_id>", methods=["POST"])
@require_appkey
def user_add(google_id):
    """
    JSON Data expected:
    {
        "user": {
            # required
            "firstname": "Jane",
            "lastname": "Doe",
            "email": "jane.doe@yahoo.com",
            "roles": ["referee", "player"],
            "active_subscriber": false,

            # optional
            "nickname": "",
            "phone": "555-555-5555",
            "gender": "non-binary",
            "league": ["abc_chicago"],
            "instagram": "",
            "twitter": "",
            "badges": []
        }
    }
    """
    try:
        data = request.get_json()
        user_key = client.key("user", google_id)
        entity = datastore.Entity(user_key)

        # defaults
        if "nickname" not in data["user"]:
            data["user"]["nickname"] = ""
        if "avatar_base64" not in data["user"]:
            data["user"]["avatar_base64"] = ""
        if "phone" not in data["user"]:
            data["user"]["phone"] = ""
        if "gender" not in data["user"]:
            data["user"]["gender"] = "other"
        if "leagues" not in data["user"]:
            data["user"]["leagues"] = []
        if "instagram" not in data["user"]:
            data["user"]["instagram"] = ""
        if "twitter" not in data["user"]:
            data["user"]["twitter"] = ""
        if "badges" not in data["user"]:
            data["user"]["badges"] = []

        # ensure leagues and badges are lists
        if not isinstance(data["user"]["roles"], list):
            raise ValueError("Roles must be a list")
        if not isinstance(data["user"]["leagues"], list):
            raise ValueError("Leagues must be a list")
        if not isinstance(data["user"]["badges"], list):
            raise ValueError("Badges must be a list")


        entity.update({
            # required
            "firstname": data["user"]["firstname"],
            "lastname": data["user"]["lastname"],
            "email": data["user"]["email"],
            "active_subscriber": data["user"]["active_subscriber"],
            "roles": data["user"]["roles"],

            # optional
            "nickname": data["user"]["nickname"],
            "avatar_base64": data["user"]["avatar_base64"],
            "phone": data["user"]["phone"],
            "gender": data["user"]["gender"],
            "leagues": data["user"]["leagues"],
            "instagram": data["user"]["instagram"],
            "twitter": data["user"]["twitter"],
            "badges": data["user"]["badges"],
        })
        client.put(entity)
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })


@app.route("/user/update/<google_id>", methods=["POST"])
@require_appkey
def user_update(google_id):
    """
    JSON Data expected:
    {
        "user": {
            "key": "value",
            "append_league": "league",
            "append_badge": "badge"
        }
    }
    """
    try:
        data = request.get_json()
        user_key = client.key("user", google_id)
        entity = client.get(user_key)

        if "badges" in data["user"]:
            raise ValueError("only use 'append_badges' key since badges can only be added")

        # ensure leagues, roles, and badges are lists
        if "roles" in data["user"]:
            if not isinstance(data["user"]["roles"], list):
                raise ValueError("Roles must be a list")
        if "leagues" in data["user"]:
            if not isinstance(data["user"]["leagues"], list):
                raise ValueError("Leagues must be a list")
        if "append_badges" in data["user"]:
            if not isinstance(data["user"]["append_badges"], list):
                raise ValueError("'append_badges' must be a list")
            else:
                data["user"]["badges"] = entity["badges"] + data["user"]["append_badges"]
                del data["user"]["append_badges"]

        entity.update(data["user"])
        client.put(entity)
    except Exception as e:
        print(str(e))
        return json.dumps({
            "status": "exception: {}".format(repr(e))
        })
    return json.dumps({
        "status": "success"
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))