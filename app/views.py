from flask import render_template, flash, request, redirect, url_for, abort, jsonify
from app import app, host, port, user, passwd, db
from .forms import SearchForm
from datetime import datetime
import pandas as pd
import pandas.io.sql as psql
import numpy as np
import pymysql
import operator
import networkx as nw
import json
from collections import OrderedDict

from git_db import GitDB
from git_score import GitScore

db = GitDB(min_repo=6, max_repo=90, min_rpm=1/6.)

@app.route('/')
@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm(csrf_enabled=False)
    if form.validate_on_submit():
        languages = form.languages
        #location = form.location
        return redirect(url_for('.results', search=languages.data))
    return render_template('search.html', title='Search Form',
            form=form)

def generate_report(login):
    report = {}
    name, email, location, start_date, avatar = db.get_user_info(login)
    report['name'] = name or ''
    report['email'] = email or ''
    report['location'] = location or ''
    report['start_date'] = start_date.strftime("%B %d, %Y")
    report['avatar_url'] = avatar

    pop_repo, lang = db.get_user_popular_repo(login) or ('','')
    report['pop_repo'] = {'name':pop_repo, 'language':lang}

    pref_langs = db.get_user_pref_lang(login)[:3]
    report['pref_langs'] = []
    for l in pref_langs:
        report['pref_langs'].append(l[0])

    return report


@app.route('/results/<search>')
def results(search):
    search = search.split(',')
    res = "<br>".join(map(lambda x: str(x), search))
    score = GitScore(db)
    final_score = score.get_final_score(search).sort("final_score", ascending=False)
    report = OrderedDict()
    for gitlogin in final_score.index[:35]:
        report[gitlogin] = generate_report(gitlogin)

    return render_template('table6.html', langs=search, data=report)
    #return render_template('table.html', data=data)

@app.route('/author')
def author():
    return render_template('author.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/slideshow')
def slideshow():
    return render_template('slideshow.html')

@app.route('/table4')
def result3():
    return render_template('table4.html')

@app.route('/table6')
def result6():
    return render_template('table6.html', langs=['Python', 'Scala',
        'C++'],data=data())

@app.route('/data')
def data(ndata=100):
    data = [
            {
"userid": "lepture",
"lang": "Python",
"poprepo": "Numpy",
"avatar":"https://avatars.githubusercontent.com/u/290496?",
"name":"Hsiaming Yang",
"email:": "",
"grade": "A",
"created": datetime(2010,5,29),
"rating": 5,
"location": "Everywhere, China",
},
            {
"userid": "tarcieri",
"lang": "Python",
"poprepo": "Scikit-learn",
"avatar":"https://avatars.githubusercontent.com/u/797?",
"name":"Tony Arcieri",
"email:": "bascule@gmail.com",
"grade": "A",
"created": datetime(2008,2,24),
"rating": 4,
"location": "San Francisco, CA"
},
            {
"userid": "Seldaek",
"lang": "C",
"poprepo": "Arduino",
"avatar":"https://avatars.githubusercontent.com/u/183678?",
"name":"Jordi Boggiano",
"email:": "j.boggiano@seld.be",
"grade": "A",
"created": datetime(2010,1,16),
"rating": 3,
"location": "Zurich, Switzerland",
},
            {
"userid": "looph",
"lang": "C++",
"poprepo": "android",
"avatar":"https://avatars.githubusercontent.com/u/104009??",
"name":"James Smith",
"email:": "james@loopj.com",
"grade": "A",
"created": datetime(2009,7,11),
"rating": 3,
"location": "San Francisco, CA",
},
            {
"userid": "mbleigh",
"lang": "C",
"poprepo": "acts-as-taggable-on",
"avatar":"https://avatars.githubusercontent.com/u/1022?",
"name":"Michael Bleigh",
"email:": "mbleigh@mbleigh.com",
"grade": "A",
"created": datetime(2008,2,26),
"rating": 3,
"location": "Los Angeles, CA",
},
            ]
    #return json.dumps(data)
    return data

@app.template_filter('datetimefilter')
def datetimefilter(value, format="%B %d, %Y"):
    return value.strftime(format)

@app.route('/results2/<search>_<location>')
def results2(search, location):
    search = search.split(',')
    res = "<br>".join(map(lambda x: str(x), search))
    print res
    #if not cachedTable:
    cnx = db_con()
    all_langs = psql.read_sql(query_all_lang(), cnx)['language'].values
    df = None
    for lang in all_langs:
        if df is None:
            df = psql.read_sql(query_by_lang(lang), cnx)
        else:
            tmp = psql.read_sql(query_by_lang(lang), cnx)
            df = df.merge(tmp, on='login', how="outer")
            df.fillna(0, inplace=True)
    df_all = df.set_index('login')
    df_all = df_all.div(df_all.apply(lambda x: np.sqrt(x.dot(x)), axis=1),
                            axis=0)
    df_user = pd.DataFrame(index=['aimran99999'], columns=all_langs)
    df_user = df_user.fillna(0)
    print df_user.shape
    print df_all.shape

    N = len(search)
    for l in search:
        l = l.strip()
        df_user[l] = 1.0/np.sqrt(N)
    result = np.dot(df_all, df_user.T)
    df_result = pd.DataFrame(result, index=df_all.index,
                            columns=['result'])
    output = df_result.sort(['result'], ascending=False)

    users = psql.read_sql(query_distinct_users(), cnx)['login'].values
    flwr = psql.read_sql(query_followers(), cnx)['follower_login'].values
    flwr_links = psql.read_sql(query_follower_links(), cnx).values
    flwg = psql.read_sql(query_following(), cnx)['following_login'].values
    flwg_links = psql.read_sql(query_following_links(), cnx).values

    graph = nw.DiGraph()
    graph.add_nodes_from(np.append(users, flwr))
    graph.add_edges_from(flwr_links)

    graph_flwg = nw.DiGraph()
    graph_flwg.add_nodes_from(np.append(users, flwg))
    graph_flwg.add_edges_from(flwg_links)

    df_pgrank_flwr = pd.DataFrame.from_records(sorted(nw.pagerank(graph).iteritems(),
                                 key=operator.itemgetter(1), reverse=True),
                          columns=['login','pagerank_flwr'])
    df_pgrank_flwr.set_index('login', inplace=True)


    df_pgrank_flwg = pd.DataFrame.from_records(sorted(nw.pagerank(graph_flwg).iteritems(),
                                 key=operator.itemgetter(1), reverse=True),
                          columns=['login','pagerank_flwg'])
    df_pgrank_flwg.set_index('login', inplace=True)

    dft = df_result.merge(df_pgrank_flwg, left_index=True, how='outer', right_index=True)
    dft = dft.merge(df_pgrank_flwr, left_index=True, how='outer', right_index=True)

    dft.fillna(0, inplace=True)
    dft.sort('result', ascending=False, inplace=True)

    data = dft[:10].T.to_dict()
    print data
    return render_template('table2.html', data=data)

    #return render_template("result.html",
    #        title = "Results",
    #        languages=languages)

def db_con():
    return pymysql.connect(host='localhost', user='root',
                    passwd="", db='git_talents')

def query_by_lang(language):
    query = """select login, count(language) as `{0}`
               from repos
               where language = \"{1}\"
               group by login
               order by `{0}`""".format(language,language)
    return query

def query_all_lang():
    query = """ select DISTINCT(language)
                FROM repos
                WHERE language IS NOT NULL
                GROUP BY language;
            """.format()
    return query

def query_distinct_users():
    query = """select distinct(login)
               from users;
               """
    return query

def query_followers():
    query = """select distinct(follower_login)
               from follower;
            """
    return query

def query_follower_links():
    query = """select login, follower_login
               from follower;
            """
    return query

def query_following():
    query = """select distinct(following_login)
               from following;
            """
    return query

def query_following_links():
    query = """select login, following_login
               from following;
            """
    return query
