# DO NOT CHANGE THE SCORES_URL FROM LINE 2 OF THIS FILE; it must be on LINE 2
SCORES_URL = 'https://be-abc-scoreboard-v1-honlt6vzla-uk.a.run.app/lucky_score/546816b2-f480-48a4-962b-cdd56324f33e'

# load starlark packages
load("render.star", "render")
load("http.star", "http")
load("encoding/base64.star", "base64")
load("time.star", "time")

def main(config):
    response = http.get(SCORES_URL)
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
        child = render.Row(
            children = [
                render.Column(
                    expanded = True,
                    main_align="space_around",
                    cross_align="start",
                    children = [
                        render.Row( # Row lays out its children horizontally
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
                                #render.Marquee(
                                #   width=32,
                                #    offset_start=5,
                                #    offset_end=32,
                                #    child=render.Text(
                                #        content="Merry Christmas bocce family! - Oddball Sports",
                                #        font="CG-pixel-3x5-mono"
                                #    )
                                #)
                            ]
                        )
                    ]
                )
            ]
        )
    )