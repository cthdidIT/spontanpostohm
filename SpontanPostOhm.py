#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for
from flask_cache import Cache
from pathlib import Path
from dotmap import DotMap
import json
import urllib.request
import sys
import ldap

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
try:
    with open('config.json', 'r') as f:
        config = DotMap(json.load(f))
except FileNotFoundError:
    print('config.json not found')
    sys.exit(0)
except Exception as e:
    raise e
l = ldap.initialize(config.ldap.url, bytes_mode=False)

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
    icon = config.fa_icon[status()]
    url = config.fa_icon.generator_url + icon
    static_path = 'favicons/fa-' + icon + '.ico'
    favicon = Path('static/' + static_path)
    if not favicon.is_file():
        with urllib.request.urlopen(url) as response, favicon.open('wb') as out_file:
            data = response.read()
            out_file.write(data)
    return redirect(url_for('static', filename=static_path))

@cache.cached(timeout=50)
def status():
    members = set(get_members())
    people = set(get_people().keys())
    union = members.intersection(people)
    postohm_count = len(union)
    return 'positive' if (postohm_count >= config.people_required) else 'negative'

@cache.cached(timeout=50)
def get_members():
    lconf = config.ldap
    l.bind_s(lconf.bind_dn, lconf.bind_pw)
    search_dn = 'ou='+config.committee+','+lconf.search_dn
    results = l.search_s(search_dn,
        ldap.SCOPE_SUBTREE, lconf.filter, [lconf.attr])
    members = []
    for dn, ldap_obj in results:
        if lconf.attr in ldap_obj:
            for position, member in dec_and_split(ldap_obj[lconf.attr]):
                if position == config.position:
                    members.append(member)
    return members

def dec_and_split(unsplit):
    return [element.decode('utf-8').split(';') for element in unsplit]

@cache.cached(timeout=50)
def get_people():
    request = urllib.request.Request(config.api.url)
    request.add_header('Authorization', 'Token ' + config.api.key)
    response = urllib.request.urlopen(request)
    data = response.read().decode('utf-8')
    sessions = json.loads(data)
    people = {}
    for session in sessions:
        people[session['user_id']] = session['nick']
    return people

if __name__ == '__main__':
    # with app.app_context():
    #     print(status())
    app.run()