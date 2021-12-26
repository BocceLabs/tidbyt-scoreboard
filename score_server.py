# imports
from flask import Flask
from markupsafe import escape
import json
from PIL import Image, ImageDraw
import os
import base64
from io import BytesIO

app = Flask(__name__)

def score_list(a, b, poss):
    return [str(a).zfill(2), str(b).zfill(2), int(poss)]

scores = {
    "A": {
        "score": score_list(0, 0, 0),
        "time": [20, 00]
    }

}

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