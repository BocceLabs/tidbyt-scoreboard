# imports
import os
import time
import requests
from google.cloud import datastore


# connect to the datastore database
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/drhoffma/oddballsports_git/tidbyt-scoreboard/oddballsportstvdev-e010e1ec7ca7.json"
client = datastore.Client(
    project="oddballsportstvdev"
)

# score server address
SCORE_SERVER = "https://be-abc-scoreboard-v1-honlt6vzla-uk.a.run.app"

# star file
STAR = "scoreboard_lucky"

# for each tidbyt, display the game data
while True:
    # request tidbyts
    endpoint = "/tidbyt/list"
    headers= {
        "Content-Type": "application/json",
        "X-Api-Key": os.getenv("ABC_SCOREBOARD_KEY")
    }
    tidbyts = requests.get(SCORE_SERVER + endpoint, headers=headers).json()["tidbyts"]

    for tidbyt_id, tidbyt_settings in tidbyts.items():
        print("updating {}".format(tidbyt_id))

        # modify the star file with the game id
        # opening the file in read mode
        with open(STAR + ".star", "r") as file:
            lines = file.readlines()
        lines[1] = "SCORES_URL = '{}/lucky_score/{}'\n".format(SCORE_SERVER,
                                                               tidbyt_settings["game_id"])
        lines[3] = "API KEY ='{}'".format(os.getenv("ABC_SCOREBOARD_KEY"))

        # opening the file in write mode
        with open(STAR + ".star", "w") as file:
            for line in lines:
                file.write(line)


        os.popen("pixlet render {}".format(STAR + ".star")).read()
        os.popen("pixlet push --api-token {} {} {}".format(tidbyt_settings["api_key"],
                                                           tidbyt_settings["device_id"],
                                                           STAR + ".webp")).read()

    time.sleep(5)

