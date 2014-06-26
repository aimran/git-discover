from flask import render_template, flash, request, redirect, url_for, abort, jsonify
from . import discover
from .forms import SearchForm
from datetime import datetime
import pandas as pd
import pandas.io.sql as psql
import numpy as np
import pymysql
import operator
import networkx as nw
import json

cachedTable = None

@discover.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        print "hey"
        languages = form.languages
        #location = form.location
        #print location.data
        return redirect(url_for('.results', search=languages.data,
                location="blah"))
        #return redirect('/')
    return render_template('discover/search.html', title='Search Form',
            form=form)


@discover.route('/author')
def author():
    return render_template('discover/author.html')

@discover.route('/about')
def about():
    return render_template('discover/about.html')

@discover.route('/slideshow')
def slideshow():
    return render_template('discover/slideshow.html')

@discover.route('/results/<search>_<location>')
def results(search, location):
    search = search.split(',')
    res = "<br>".join(map(lambda x: str(x), search))
    print res
    #if not cachedTable:
    cnx = db_con()
    all_langs = psql.read_sql(query_all_lang(), cnx)['language'].values
    df = None
#    for lang in all_langs:
#        if df is None:
#            df = psql.read_sql(query_by_lang(lang), cnx)
#        else:
#            tmp = psql.read_sql(query_by_lang(lang), cnx)
#            df = df.merge(tmp, on='login', how="outer")
#            df.fillna(0, inplace=True)
#    df_all = df.set_index('login')
#    df_all = df_all.div(df_all.apply(lambda x: np.sqrt(x.dot(x)), axis=1),
#                            axis=0)

#    df_user = pd.DataFrame(index=['aimran99999'], columns=all_langs)
#    df_user = df_user.fillna(0)
#    print df_user.shape
#    print df_all.shape
#
#    N = len(search)
#    for l in search:
#        l = l.strip()
#        df_user[l] = 1.0/np.sqrt(N)
#    result = np.dot(df_all, df_user.T)
#    df_result = pd.DataFrame(result, index=df_all.index,
#                            columns=['result'])
#    output = df_result.sort(['result'], ascending=False)
#
#    data = output[:10].to_dict()['result']
#    data = sorted(data.iteritems(),
#            key=operator.itemgetter(1),
#            reverse=True)
    return render_template('discover/table6.html', langs=search, data=data())
    #return render_template('discover/table.html', data=data)

@discover.route('/table4')
def result3():
    return render_template('discover/table4.html')

@discover.route('/table6')
def result6():
    return render_template('discover/table6.html', langs=['Python', 'Scala',
        'C++'],data=data())

@discover.route('/data')
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

@discover.app_template_filter('datetimefilter')
def datetimefilter(value, format="%B %d, %Y"):
    return value.strftime(format)

@discover.route('/results2/<search>_<location>')
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
    return render_template('discover/table2.html', data=data)

    #return render_template("result.html",
    #        title = "Results",
    #        languages=languages)

def db_con():
    return pymysql.connect(host='localhost', user='root',
                    passwd="mamu", db='git_talents')

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
