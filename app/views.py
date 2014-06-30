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

    return render_template('results.html', langs=search, data=report)
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

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404


@app.template_filter('datetimefilter')
def datetimefilter(value, format="%B %d, %Y"):
    return value.strftime(format)

@app.route('/network')
def network():
    # Renders network.html.
    return render_template('network.html')

