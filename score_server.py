# imports
from flask import Flask
from markupsafe import escape
import json

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


@app.route("/setscore/<court>/<score>", methods=["GET", "POST"])
def setscore(court, score):
    s = score.split(",")
    scores[court]["score"] = score_list(s[0], s[1], s[2])
    return "success"

@app.route("/resettime/<court>", methods=["GET", "POST"])
def gettime(court):
    scores[court]["time"] = [2, 0]
    return "success"