from flask import Flask, request, render_template, g, Markup

import sqlite3
import datetime
from dateutil.relativedelta import relativedelta

dbfile = "static/teacup_articles.sqlite"
time_fmt = "%F %T"


def connect_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(dbfile)
        db.row_factory = sqlite3.Row
    return db


app = Flask(__name__)


@app.template_filter("break_line")
def conv_br(text):
    return Markup(text.replace("\n", "<br>"))

@app.route("/")
def top_page():
    if request.method == "GET":
        return render_template("index.html", title="トップ")


@app.route("/<int:yyyy>/<int:mm>")
def view_article_list(yyyy=2022, mm=6):
    start_date = datetime.datetime(yyyy, mm, 1, 0, 0, 0)
    end_date = start_date + relativedelta(months=1)
    conn = connect_db()
    cur = conn.execute("select article_title, author_name, author_remote_addr, \
     strftime('%Y-%m-%d %H:%M:%S', created_at) as created_at, article_text, article_id \
      from articles where created_at between ? and ?", (start_date, end_date))
    res = cur.fetchall()
    cur.close()
    return render_template("index.html", rows=res, title=f"{yyyy}年{mm}月")


@app.route("/post/<article_id>")
def view_one_article(article_id):
    conn = connect_db()
    cur = conn.execute("select article_title, author_name, author_remote_addr, \
     strftime('%Y-%m-%d %H:%M:%S', created_at) as created_at, article_text, article_id \
      from articles where article_id == ?", (article_id,))
    res = cur.fetchone()
    cur.close()
    return render_template("detail.html", res=res, title="投稿詳細")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
