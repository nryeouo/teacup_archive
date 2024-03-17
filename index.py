from flask import Flask, request, render_template, g

from markupsafe import Markup

import sqlite3
import datetime
from dateutil.relativedelta import relativedelta

from functions.v1 import app as v1

dbfile = "static/teacup_articles.sqlite"
time_fmt = "%F %T"


word_regex = r"^([^(since|until|by|title)].*?)(?=$| (since|until|by|title))"
since_regex = r"^.+ since:(20\d{2}-[0-1]\d-[0-3]\d)"
until_regex = r"^.+ until:(20\d{2}-[0-1]\d-[0-3]\d)"
by_regex = r"^.+ by:(.+?($| ))"
title_regex = r"^.+ title:(.+?($| ))"


app = Flask(__name__)
app.register_blueprint(v1)


@app.template_filter("break_line")
def conv_br(text):
    return Markup(text.replace("\n", "<br>"))

@app.template_filter("weekday")
def convert_weekday(strftime):
    datetime_parts = strftime.split(',')
    weekday_number = datetime_parts[1]
    weekdays = ["日", "月", "火", "水", "木", "金", "土"]
    jp_string = f"{datetime_parts[0]}({weekdays[int(weekday_number)]}) {datetime_parts[2]}"
    return jp_string


@app.route("/")
def top_page():
    if request.method == "GET":
        return render_template("index.html", title="トップ")


# app.run(host='0.0.0.0', port=8901, debug=True)
