import csv
import io
import sqlite3
from datetime import datetime

import numpy as np
import sqlalchemy as db
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, send_from_directory
from pathlib import Path


def clear_temp():
    temp = Path("./temp")
    for item in temp.iterdir():
        item.unlink()


scheduler = BackgroundScheduler()
scheduler.add_job(clear_temp, trigger='interval', minutes=2)
scheduler.start()

app = Flask(__name__)
db = r"./results.db"
jumbotron_bg = "https://sun9-30.userapi.com/c857520/v857520212/c8d33/2830GSktk0w.jpg"
header = "Hide that!"


def gather_plot_info():
    conn = sqlite3.connect(db)
    with conn:
        languages = conn.cursor().execute("select * from languages").fetchall()
        sex_vals_list = []
        for lang in languages:
            m = conn.cursor().execute(
                ("select ifnull(count(*), 0) from results where sex = \"Male\" and language_id = \"{}\"").format(
                    lang[1])).fetchall()[0][0]
            f = conn.cursor().execute(
                ("select ifnull(count(*), 0) from results where sex = \"Female\" and language_id = \"{}\"").format(
                    lang[1])).fetchall()[0][0]
            sex_vals_list.append((m, f))

    vals = np.array(sex_vals_list)
    lang_distr = [sum(sex_vals) for sex_vals in sex_vals_list]
    sex_distr = list(vals.flatten())
    sex = []
    for _ in sex_vals_list:
        sex.append('♂')
        sex.append('♀')

    return list(map(lambda l: l[0], languages)), lang_distr, sex, sex_distr


@app.route('/')
def index():
    conn = sqlite3.connect(db)
    with conn:
        languages = conn.cursor().execute("select * from languages").fetchall()
        questions = conn.cursor().execute("select * from questions").fetchall()
    return render_template("index.html", questions=questions, jumbotron_bg=jumbotron_bg, header=header,
                           languages=list(map(lambda l: l[0], languages)))


@app.route('/search')
def search():
    conn = sqlite3.connect(db)
    with conn:
        languages = conn.cursor().execute("select * from languages").fetchall()
        questions = conn.cursor().execute("select * from questions").fetchall()
    return render_template("search.html", title="Browse answers", languages=languages, questions=questions,
                           jumbotron_bg=jumbotron_bg, header=header)


def generate_query(params):
    query = f'''select {','.join(params['cols'])} from results left join languages l on results.language_id = l.id'''
    additional_query = []
    sex_query = ""
    lang_query = []
    col_query = []
    if len(params) > 1:
        if 'sex' in params:
            sex_query = f'''sex = "{params['sex']}"'''
        if 'language' in params:
            lang_query = list(map(lambda l: f'''language_id = {l}''', params['language']))
            if len(lang_query) > 1:
                lang_query = '(' + " or ".join(lang_query) + ')'
            else:
                lang_query = lang_query[0]
        if 'word' in params:
            col_query = list(
                map(lambda q: f'''{q} like "{params['word']}"''', list(filter(lambda c: c[0] == 'q', params['cols']))))
            if len(col_query) > 1:
                col_query = '(' + ' or '.join(col_query) + ')'
            else:
                col_query = col_query[0]

    if sex_query:
        additional_query.append(sex_query)

    if lang_query:
        additional_query.append(lang_query)

    if col_query:
        additional_query.append(col_query)

    if additional_query:
        if len(additional_query) > 1:
            additional_query = ' and '.join(additional_query)
        else:
            additional_query = additional_query[0]
    else:
        additional_query = ""

    if additional_query != "":
        query += ' where ' + additional_query

    return query


def generate_params(req_f):
    cols = ['language', 'sex']
    cols.extend(req_f.getlist('question'))
    if len(cols) == 2:
        conn = sqlite3.connect(db)
        with conn:
            questions = conn.cursor().execute("select * from questions").fetchall()
            cols.extend(list(map(lambda q: f"q{q[0]}", questions)))

    params = {'cols': cols}

    if req_f['word_to_search'] != "":
        params['word'] = req_f['word_to_search']

    if "sex" in req_f:
        params['sex'] = req_f['sex']

    language = req_f.getlist('lang')
    if language:
        params['language'] = language

    return params


@app.route('/result', methods=['POST'])
def results():
    params = generate_params(request.form)
    query = generate_query(params)
    conn = sqlite3.connect(db)
    with conn:
        search_results = conn.cursor().execute(query).fetchall()
        questions = conn.cursor().execute("select * from questions").fetchall()

    processed_questions = [q for q in questions if f'''q{q[0]}''' in params['cols']]

    processed_params = {'cols': ','.join(params['cols'])}
    if 'word' in params:
        processed_params['word'] = params['word']
    else:
        processed_params['word'] = ""
    if 'sex' in params != "":
        processed_params['sex'] = params['sex']
    else:
        processed_params['sex'] = ""
    if 'language' in params:
        if len(params['language']) == 1:
            processed_params['language'] = params['language'][0]
        else:
            processed_params['language'] = ",".join(params['language'])
    else:
        processed_params['language'] = ""

    return render_template("result.html", title="Search results", search_results=search_results,
                           questions=processed_questions,
                           jumbotron_bg=jumbotron_bg, header=header, params=processed_params)


@app.route('/download', methods=['GET'])
def download_csv():
    params = {'cols': request.args.get('cols').split(',')}
    if request.args.get('sex') != "":
        params['sex'] = request.args.get('sex')
    if request.args.get("language") != "":
        params['language'] = request.args.get('language').split(',')
    if request.args.get("word") != "":
        params['word'] = request.args.get("word")

    conn = sqlite3.connect(db)
    with conn:
        search_results = conn.cursor().execute(generate_query(params)).fetchall()

    now = datetime.now()
    Path('./temp').mkdir(parents=True, exist_ok=True)
    fname = f'''hide-search-results_{now.strftime("%d-%m-%Y_%H-%M-%S")}.csv'''
    with io.open(f'''./temp/{fname}''', 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=params['cols'])
        writer.writeheader()
        for res in search_results:
            writer.writerow(dict(zip(params['cols'], res)))

    return send_from_directory(directory="./temp", filename=fname, as_attachment=True, attachment_filename=fname)


@app.route('/stats')
def stats():
    lang_num = 0
    conn = sqlite3.connect(db)
    with conn:
        lang_num = conn.cursor().execute("select ifnull(count(*), 0) from languages").fetchall()[0][0]
        answers = conn.cursor().execute("select count(*) from results").fetchall()[0][0]
    languages, lang_distr, sexes, sex_distr = gather_plot_info()
    return render_template("stats.html", header_title="Stats", lang_num=lang_num, languages=languages,
                           lang_distr=lang_distr, sexes=sexes, sex_distr=sex_distr,
                           answers=answers, jumbotron_bg=jumbotron_bg, header=header)


@app.route('/accepted', methods=['POST'])
def accept():
    req_f = request.form
    conn = sqlite3.connect(db)
    with conn:
        if conn.cursor().execute(f'''select count(*) from languages where language=\"{request.form['language']}\"''').fetchall()[0][0] == 0:
            conn.cursor().execute("insert into languages(language) values({})".format(request.form['language']))
        lang_id = conn.cursor().execute(
            f'''select id from languages where language="{req_f['language']}"''').fetchall()[0][0]

        q_keys = [k for k in req_f.keys() if k[0] == 'q']
        q_vals = [f'"{req_f[key]}"' for key in q_keys]

        query = f'''insert into results(language_id, sex, {", ".join(q_keys)}) values({lang_id}, "{req_f['sex']}", {", ".join(q_vals)})'''
        conn.cursor().execute(query)
        id = conn.cursor().execute("select count(*) from results").fetchall()[0][0]
    return render_template("accepted.html", id=id, title="Answer accepted", jumbotron_bg=jumbotron_bg, header=header)


if __name__ == '__main__':
    app.run()
