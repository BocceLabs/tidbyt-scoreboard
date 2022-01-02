# DO NOT CHANGE THE SCORES_URL FROM LINE 2 OF THIS FILE; it must be on LINE 2
SCORES_URL = ''
# DO NOT CHANGE THE API KEY FROM LINE 4 OF THIS FILE; it must be on LINE 4
API_KEY = ''

# load starlark packages
load("render.star", "render")
load("http.star", "http")
load("encoding/base64.star", "base64")
load("time.star", "time")

def main(config):
    # form the headers
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
    }

    # make the request
    response = http.get(SCORES_URL, headers=headers)

    # ensure the status code is valid
    if response.status_code != 200:
        fail("Scores request failed with status %d", response.status_code)

    response = response.json()
    image_str = response["0"]
    time_str = response["time_str"]

    if time_str == "0:00:00":
        time_color = "#C00"
    else:
        time_color = "#FFF"

    return render.Root(
        child = render.Row( # row lays out its children horizontally
            children = [
                render.Column( # column lays out its children vertically
                    expanded = True,
                    main_align="space_around",
                    cross_align="start",
                    children = [
                        render.Row( # row lays out its children horizontally
                            children = [
                                render.Marquee(
                                    width=32,
                                    child=render.Text(
                                        content=response["team_a"],
                                        font="CG-pixel-3x5-mono"
                                    ),
                                    offset_start=31,
                                    offset_end=31,
                                ),
                                render.Marquee(
                                    width=32,
                                    child=render.Text(
                                        content=response["team_b"],
                                        font="CG-pixel-3x5-mono"
                                    ),
                                    offset_start=31,
                                    offset_end=31,
                                )
                            ]
                        ),
                        render.Row( # row lays out its children horizontally
                            children = [
                                render.Padding(
                                    pad=(0, 0, 0, 0),
                                    child=render.Image(src=base64.decode(image_str))
                                )
                            ],
                        ),
                        render.Row(
                            children = [
                                render.Text(
                                    content=time_str,
                                    font="CG-pixel-3x5-mono",
                                    color=time_color
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    )