from flask import Flask, render_template, request
import sqlite3
import sqlalchemy as db
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import rc

rc('font', **{'family': 'serif', 'serif': ['Yu Mincho']})

app = Flask(__name__)
db = r"./results.db"
jumbotron_bg = "https://sun9-30.userapi.com/c857520/v857520212/c8d33/2830GSktk0w.jpg"
header = "Hide that!"


def makeplot(languages):
    fig, ax = plt.subplots()

    size = 0.3

    conn = sqlite3.connect(db)
    with conn:
        vals_list = []
        for lang in languages:
            m = conn.cursor().execute(
                ("select ifnull(count(*), 0) from results where sex = \"Male\" and language_id = \"{}\"").format(
                    lang[1])).fetchall()[0][0]
            f = conn.cursor().execute(
                ("select ifnull(count(*), 0) from results where sex = \"Female\" and language_id = \"{}\"").format(
                    lang[1])).fetchall()[0][0]
            vals_list.append((m, f))

    vals = np.array(vals_list)
    inner_vals = vals.flatten()
    cmap = plt.get_cmap("tab20c")
    outer_colors = cmap(np.arange(len(languages) + 1) * 4)
    inner_colors_list = []
    sex_labels = []
    for i in range(len(languages)):
        inner_colors_list.append(i * 4 + 1)
        inner_colors_list.append(i * 4 + 2)
        if inner_vals[2 * i] > 0:
            sex_labels.extend(['♂ ({})'.format(vals[i][0])])
        else:
            sex_labels.extend([''])
        if inner_vals[2 * i + 1] > 0:
            sex_labels.extend(['♀ ({})'.format(vals[i][1])])
        else:
            sex_labels.extend([''])
    inner_colors = cmap(np.array(inner_colors_list))

    lang_labels_temp = list(zip(languages, vals_list))
    lang_labels_final = [f"{x[0][0]} ({sum(x[1])})" if sum(x[1]) > 0 else "" for x in lang_labels_temp]

    ax.pie(vals.sum(axis=1), radius=1, colors=outer_colors, labels=lang_labels_final,
           wedgeprops=dict(width=size, edgecolor='w'))

    ax.pie(inner_vals, radius=1 - size, colors=inner_colors, labels=sex_labels, labeldistance=0.7,
           wedgeprops=dict(width=size, edgecolor='w'))

    ax.set(aspect="equal", title='Answers language- and gender-wise')

    plt.savefig('static/stats.png')
    return 'static/stats.png'


@app.route('/')
def index():
    conn = sqlite3.connect(db)
    with conn:
        questions = conn.cursor().execute("select * from questions").fetchall()
    return render_template("index.html", questions=questions, jumbotron_bg=jumbotron_bg, header=header)


@app.route('/search')
def search():
    conn = sqlite3.connect(db)
    with conn:
        languages = conn.cursor().execute("select * from languages").fetchall()
        questions = conn.cursor().execute("select * from questions").fetchall()
    return render_template("search.html", title="Browse answers", languages=languages, questions=questions,
                           jumbotron_bg=jumbotron_bg, header=header)


@app.route('/result', methods=['POST'])
def results():
    conn = sqlite3.connect(db)
    with conn:
        questions = conn.cursor().execute("select * from questions").fetchall()

        additional_query = []

        question_ids = list(map(lambda q: q[0].split('_')[1],
                                     [(key, request.form[key]) for key in request.form if key.startswith("q")]))

        query_cols = ["language", "sex"]
        if not question_ids:
            question_ids = list(map(lambda q: f"{q[0]}", questions))
        query_cols.extend(list(map(lambda q: f"q{q}", question_ids)))
        question_comparisons = list(map(lambda q: f"q{q} like \"{request.form['word_to_search']}\"", question_ids))

        question_id_query = ", ".join(query_cols)

        if len(question_comparisons) == 1:
            question_comparison_query = question_comparisons[0]
        else:
            question_comparison_query = " or ".join(question_comparisons)

        lang_ids = list(map(lambda l: l[0].split('_')[1],
                            [(key, request.form[key]) for key in request.form if key.startswith("lang")]))
        lang_query = []
        for lang_id in lang_ids:
            lang_query.append("language_id = {}".format(lang_id))
        if len(lang_query) > 1:
            additional_query.append('(' + " or ".join(lang_query) + ')')
        elif len(lang_query) == 1:
            additional_query.append('(' + lang_query[0] + ')')

        sex_ids = list(map(lambda l: l[0].split('_')[1],
                           [(key, request.form[key]) for key in request.form if key.startswith("sex")]))
        if sex_ids:
            additional_query.append("sex = \"{}\"".format(sex_ids[0]))

        additional_query_final = " and ".join(additional_query)

        activate_additional_query = (len(lang_query) > 0) or (len(sex_ids) > 0)
        query = f"select {question_id_query} from results inner join languages on results.language_id = languages.id"
        if request.form['word_to_search'] != "":
            query += f" where {question_comparison_query}"
        if activate_additional_query:
            query += " and " + additional_query_final
        search_results = conn.cursor().execute(query).fetchall()
    return render_template("result.html", title="Search results", search_results=search_results,
                           questions=[q for q in questions if str(q[0]) in question_ids],
                           jumbotron_bg=jumbotron_bg, header=header)


@app.route('/stats')
def stats():
    lang_num = 0
    conn = sqlite3.connect(db)
    with conn:
        lang_num = conn.cursor().execute("select ifnull(count(*), 0) from languages").fetchall()[0][0]
        languages = conn.cursor().execute("select * from languages").fetchall()
        answers = conn.cursor().execute("select count(*) from results").fetchall()[0][0]
    stats = makeplot(languages)
    languages1 = list(map(lambda x: x[0], languages))
    return render_template("stats.html", title="Stats", lang_num=lang_num, languages=languages1, plot_url=stats,
                           answers=answers, jumbotron_bg=jumbotron_bg, header=header)


@app.route('/accepted', methods=['POST'])
def accept():
    conn = sqlite3.connect(db)
    with conn:
        if conn.cursor().execute(
                "select count(*) from languages where language=\"{}\"".format(request.form['language'])).fetchall()[0][
            0] == 0:
            conn.cursor().execute("insert into languages(language) values({})".format(request.form['language']))
        lang_id = conn.cursor().execute(
            "select id from languages where language=\"{}\"".format(request.form['language'])).fetchall()[0][0]

        query = "insert into results(language_id, sex, q1, q2, q3, q4, q5, q6, q7) values({}, \"{}\", \"{}\",\
             \"{}\", \"{}\", \"{}\", \"{}\", \"{}\", \"{}\")" \
            .format(lang_id, request.form['sex'], request.form['q1'], request.form['q2'],
                    request.form['q3'], \
                    request.form['q4'], request.form['q5'], request.form['q6'], request.form['q7'])
        conn.cursor().execute(query)
        id = conn.cursor().execute("select count(*) from results").fetchall()[0][0]
    return render_template("accepted.html", id=id, title="Answer accepted", jumbotron_bg=jumbotron_bg, header=header)


if __name__ == '__main__':
    app.run()
