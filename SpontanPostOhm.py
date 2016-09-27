#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for
from flask_cache import Cache
from pathlib import Path
import json
import urllib.request
import sys

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
config = {}
api_key = ''

@app.route('/')
@cache.cached(timeout=50)
def index():
    thestatus = status()
    return render_template('index.html', 
        config=config, 
        people=get_people(), 
        status=thestatus)

@app.route('/favicon.ico')
def favicon():
    icon = config['fa_icon'][status()]
    url = config['fa_icon']['generator_url'] + icon
    static_path = 'favicons/fa-' + icon + '.ico'
    favicon = Path('static/' + static_path)
    if not favicon.is_file():
        with urllib.request.urlopen(url) as response, favicon.open('wb') as out_file:
            data = response.read()
            out_file.write(data)
    return redirect(url_for('static', filename=static_path))

@cache.cached(timeout=50)
def status():
    postohm_members = set(config['people']).intersection(set(get_people().keys()))
    postohm_count = len(postohm_members)
    return 'positive' if (postohm_count >= config['people_required']) else 'negative'

@cache.cached(timeout=50)
def get_people():
    request = urllib.request.Request(config['url'])
    request.add_header('Authorization', 'Token ' + api_key)
    response = urllib.request.urlopen(request)
    data = response.read().decode('utf-8')
    sessions = json.loads(data)
    people = {}
    for session in sessions:
        people[session['user_id']] = session['nick']
    return people

if __name__ == '__main__':
    try:
        with open('config.json', 'r') as f:
            the_config = json.load(f)
    except FileNotFoundError:
        print('config.json not found')
        sys.exit(0)
    except Exception as e:
        raise e
    api_key = the_config['api_key']
    del the_config['api_key']
    config = the_config
    app.run()