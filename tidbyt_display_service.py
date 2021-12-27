# imports
import os
import time
import requests
from google.cloud import datastore


# connect to the datastore database
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/drhoffma/oddballsports_git/tidbyt-scoreboard/oddballsportstvdev-e010e1ec7ca7.json"
client = datastore.Client(
    project="oddballsportstvdev"
)

# score server address
SCORE_SERVER = "http://192.168.2.16:8080"

# star file
STAR = "scoreboard_lucky"

# for each tidbyt, display the game data
while True:
    # request tidbyts
    endpoint = "/tidbyt/list"
    tidbyts = requests.get(SCORE_SERVER + endpoint).json()

    for tidbyt_id, tidbyt_settings in tidbyts.items():
        print("updating {}".format(tidbyt_id))

        # modify the star file with the game id
        # opening the file in read mode
        with open(STAR + ".star", "r") as file:
            lines = file.readlines()
        lines[1] = "SCORES_URL = 'http://192.168.2.16:8080/lucky_score/{}'\n".format(tidbyt_settings["game_id"])
        # opening the file in write mode
        with open(STAR + ".star", "w") as file:
            for line in lines:
                file.write(line)


        os.popen("pixlet render {}".format(STAR + ".star")).read()
        os.popen("pixlet push --api-token {} {} {}".format(tidbyt_settings["api_key"],
                                                           tidbyt_settings["device_id"],
                                                           STAR + ".webp")).read()
    time.sleep(5)

