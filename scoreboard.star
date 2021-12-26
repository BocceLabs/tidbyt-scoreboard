load("render.star", "render")
load("http.star", "http")
load("encoding/base64.star", "base64")
load("time.star", "time")


SCORES_URL = "http://192.168.2.16:8080/score/A"

BLUE_BALL = base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAC6ADAAQAAAABAAAACwAAAACBvloGAAAAg0lEQVQYGWNkQAL2gVv/I3HBzIPrvRlhYkwwBkjhrx/fGBLCVRmQaWQDwIpBAiBF2ABIHKaBCWYiNoUwMZBNIHWM+EyFKQbRC1beZgA7Y9bCi2BxQjTtTGYChSMbBxey8zDYIHmQOhaQDCTgMSMEJAfyGCxi4LEDkoCFJ4gNAzCFID4A3G5RnQcJVWsAAAAASUVORK5CYII=")
RED_BALL = base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAsAAAALCAYAAACprHcmAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAC6ADAAQAAAABAAAACwAAAACBvloGAAAAgElEQVQYGWNkQAKX9fX/I3HBTN2LFxlhYkwwBkjh558/GXTmLWZAppENACsGCYAUYQMgcZgGJpiJ2BTCxEA2gdQx4jMVphhEX0mKZQA743h0GFicEE07k5lA4cjLzo7sPAw2SB6kDuxmEAPkAWwAJA6LGHjsgBTCwhNZE0whSAwADuVNDOeVZvIAAAAASUVORK5CYII=")
POSSESSION = base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAABaADAAQAAAABAAAABQAAAAB/qhzxAAAAMklEQVQIHWNkAIL/B9n/g2gQYLT/ycgIFtAygYiAyGtnGJjgPCAHBhCCSKoZQbLoZgIAc+IOztmtBk8AAAAASUVORK5CYII=")
NO_POSSESSION = base64.decode("iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAABaADAAQAAAABAAAABQAAAAB/qhzxAAAADElEQVQIHWNgoBMAAABpAAGDG4YMAAAAAElFTkSuQmCC")

def main(config):
    response = http.get(SCORES_URL)
    if response.status_code != 200:
        fail("Scores request failed with status %d", response.status_code)

    court = response.json()["A"]

    if court["score"][2] == 0:
        # BLUE
        A_POSSESSION = POSSESSION
        B_POSSESSION = NO_POSSESSION
    elif court["score"][2] == 1:
        # RED
        B_POSSESSION = POSSESSION
        A_POSSESSION = NO_POSSESSION
    elif court["score"][2] == 2:
        # Nobody
        B_POSSESSION = NO_POSSESSION
        A_POSSESSION = NO_POSSESSION

    timezone = config.get("timezone") or "America/New_York"

    MM = court["time"][0]
    SS = court["time"][1]

    if int(MM) == 0 and int(SS) == 0:
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
                                    child=render.Image(src=BLUE_BALL)
                                ),
                                render.Padding(
                                    pad=(0, 7, 0, 0),
                                    child=render.Image(src=A_POSSESSION)
                                ),
                                render.Text(
                                    content="%s" % (court["score"][0]),
                                    font="6x13",
                                    offset=1
                                )
                            ],
                        ),
                        render.Row( # Row lays out its children horizontally
                            children = [
                                render.Padding(
                                    pad=(0, 0, 0, 0),
                                    child=render.Image(src=RED_BALL)
                                ),
                                render.Padding(
                                    pad=(0, 7, 0, 0),
                                    child=render.Image(src=B_POSSESSION)
                                ),
                                render.Text(
                                    content="%s" % (court["score"][1]),
                                    font="6x13",
                                    offset=1
                                )
                            ],
                        ),
                    ]
                ),
                render.Column(
                    children = [render.Box(width=1, height=32, color="#0a0")]
                ),
                render.Column(
                    expanded = True,
                    main_align = "space_around",
                    cross_align = "center",
                    children = [
                        render.Row(
                            children = [
                                render.Text(
                                    content="Court:"
                                ),
                            ]
                        ),
                        render.Row(
                            children = [
                                render.Text(
                                    content="Window"
                                ),
                            ]
                        ),
                        render.Row(
                            children = [
                                render.Text(
                                    content = "%s:%s" % (MM, SS),
                                    font = "6x13",
                                    color = time_color
                                )
                            ]
                        )

                    ]
                )
            ]
        )
    )