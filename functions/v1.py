from flask import Blueprint, request, render_template, g
from flask_paginate import Pagination, get_page_parameter

import sqlite3
import datetime
from dateutil.relativedelta import relativedelta


dbfile = "static/teacup_articles.sqlite"
time_fmt = "%F %T"

# register blueprint object
app = Blueprint("functions", __name__)


def connect_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(dbfile)
        db.row_factory = sqlite3.Row
    return db


def parse_query(query):
    operators = ["since", "until", "by", "title"]
    parsed_query = {}
    search_terms = []

    query_parts = query.split()
    while query_parts:
        part = query_parts.pop(0)
        is_operator = False
        for operator in operators:
            if part.startswith(operator + ':'):
                parsed_query[operator] = part.split(':')[1]
                is_operator = True
                break
        if not is_operator:
            search_terms.append(part)

    return search_terms if search_terms else [''], parsed_query


@app.route("/v1/<int:yyyy>/<int:mm>")
def view_article_list(yyyy=2022, mm=6):
    start_date = datetime.datetime(yyyy, mm, 1, 0, 0, 0)
    end_date = start_date + relativedelta(months=1)
    conn = connect_db()
    cur = conn.execute("select article_title, author_name, author_remote_addr, \
     strftime('%Y-%m-%d,%w,%H:%M:%S', created_at) as created_at, article_text, article_id \
      from articles where created_at between ? and ?", (start_date, end_date))
    res = cur.fetchall()
    cur.close()
    return render_template("index.html", rows=res, title=f"{yyyy}年{mm}月")


@app.route("/v1/post/<article_id>")
def view_one_article(article_id):
    conn = connect_db()
    cur = conn.execute("select article_title, author_name, author_remote_addr, \
     strftime('%Y-%m-%d,%w,%H:%M:%S', created_at) as created_at, article_text, article_id \
      from articles where article_id == ?", (article_id,))
    res = cur.fetchone()
    cur.close()
    return render_template("detail.html", res=res, title="投稿詳細")


@app.route("/v1/search")
def view_search_results():
    query = request.args.get("q")

    if query:
        conn = connect_db()

        # parse_query 関数を使用して検索語と演算子の値を取得
        search_terms, parsed_query = parse_query(query)

        # query and parameters are Written by ChatGPT
        # 与えられた演算子が None の場合、その条件を無視する
        query_to_execute = """
            SELECT article_title, author_name, author_remote_addr,
                strftime('%Y-%m-%d,%w,%H:%M:%S', created_at) as created_at,
                article_text, article_id
            FROM articles
            WHERE article_text LIKE ?
            AND (created_at >= ? OR ? IS NULL)
            AND (created_at <= ? OR ? IS NULL)
            AND (author_name LIKE ? OR ? IS NULL)
            AND (article_title LIKE ? OR ? IS NULL)
        """

        # AND Search
        if len(search_terms) > 1:
            for _ in search_terms[1:]:
                query_to_execute += " AND article_text LIKE ?"

        # パラメータの設定
        parameters = [
            "%" + search_terms[0] + "%",  # 検索語
            str(parsed_query.get("since", "2010-06-01")),  # since の値またはデフォルト値
            str(parsed_query.get("since", "2010-06-01")),  # since の値またはデフォルト値
            str(parsed_query.get("until", "2022-07-31")),  # until の値またはデフォルト値
            str(parsed_query.get("until", "2022-07-31")),  # until の値またはデフォルト値
            "%" + parsed_query.get("by", "") + "%",  # by の値または空文字列
            "%" + parsed_query.get("by", "") + "%",  # by の値または空文字列
            "%" + parsed_query.get("title", "") + "%",  # title の値または空文字列
            "%" + parsed_query.get("title", "") + "%"  # title の値または空文字列
        ]
        if len(search_terms) > 1:
            parameters.extend(["%" + term + "%" for term in search_terms[1:]])

        cur = conn.execute(query_to_execute, parameters)

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
