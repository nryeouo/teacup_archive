import re

from flask import Flask, request, render_template, g, Markup
from flask_paginate import Pagination, get_page_parameter

import sqlite3
import datetime
from dateutil.relativedelta import relativedelta

dbfile = "static/teacup_articles.sqlite"
time_fmt = "%F %T"

word_regex = r"^([^(since|until|by|title)].*?)(?=$| (since|until|by|title))"
since_regex = r"^.+ since:(20\d{2}-[0-1]\d-[0-3]\d)"
until_regex = r"^.+ until:(20\d{2}-[0-1]\d-[0-3]\d)"
by_regex = r"^.+ by:(.+?($| ))"
title_regex = r"^.+ title:(.+?($| ))"


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


@app.route("/search")
def view_search_results():
    query = request.args.get("q")

    if query:
        word_s = re.search(word_regex, query)
        word = word_s.group(1) if word_s else ""
        print("Word=" + word + ".")

        if len(word) > 0:
            since_s = re.search(since_regex, query)
            until_s = re.search(until_regex, query)
            by_s = re.search(by_regex, query)
            title_s = re.search(title_regex, query)

            since = since_s.group(1) if since_s else "2010-06-01"
            until = until_s.group(1) if until_s else "2022-07-31"
            by = f"%{(by_s.group(1))}%" if by_s else "%"
            title = f"%{(title_s.group(1))}%" if title_s else "%"

            conn = connect_db()


            cur = conn.execute("select article_title, author_name, author_remote_addr, \
             strftime('%Y-%m-%d %H:%M:%S', created_at) as created_at, article_text, article_id \
              from articles where article_text like ? and created_at >= ? and created_at <= ? \
               and author_name like ? and article_title like ?",
                                   ("%" + str(word) + "%", str(since), str(until), str(by), str(title)))

            res = cur.fetchall()
            cur.close()
            page = request.args.get(get_page_parameter(), type=int, default=1)
            res_p = res[(page - 1) * 25: page * 25]
            page_disp_msg = "{total}件の結果。{start}から{end}件目を表示中"
            pagination = Pagination(page=page, total=len(res), per_page=25,
                                    css_framework="bootstrap5", display_msg=page_disp_msg)
            return render_template("index_paginate.html", rows=res_p, pagination=pagination,
                                   title=query, total=len(res))
        else:
            return render_template("index.html", title="トップ")
    else:
        return render_template("index.html", title="トップ")

# app.run(host='0.0.0.0', port=8901, debug=True)
