import requests

import sys
sys.path.append('.')
from config import config

headers = {}

def login():

    global headers

    params = {
        "session": {
            "login": config["login"],
            "password": config["password"]
        }
    }

    try:
        r = requests.post(
            config['aquarium_url'] + "/sessions.json",
            json=params
            )
    except Exception as e:
        raise Exception("Could not log in to " + config["aquarium_url"] +
                        ": " + str(e))

    headers = { "cookie": __fix_remember_token(r.headers["set-cookie"]) }
    print(r.status_code)
    return r.status_code

def get(path):

    global headers
    r = requests.get(config['aquarium_url'] + path, headers=headers)
    return r.json()

def post(path,data):

    global headers
    r = requests.post(config['aquarium_url'] + path,json=data,headers=headers)
    return r.json()

def __fix_remember_token(h):
    parts = h.split(';')
    rtok = ""
    for c in parts:
        cparts = c.split('=')
        if ( cparts[0] == "remember_token_development" or
             cparts[0] == "remember_token_production" ):
            rtok = cparts[1]
    return "remember_token=" + rtok + "; " + h
