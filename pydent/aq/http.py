"""Define the http methods: login, get, put, post"""

import requests
import re

import sys
sys.path.append('.')
from config import config

headers = {}
logged_in = False


def login():
    """Log in to Aquarium using login info in config.py"""
    global headers
    global logged_in

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

    headers = {"cookie": __fix_remember_token(r.headers["set-cookie"])}
    print(r.status_code)
    logged_in = True
    return r.status_code


def get(path):
    """Perform an http.get"""
    global headers
    if logged_in:
        r = requests.get(config['aquarium_url'] + path, headers=headers)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return r.json()
    except Exception as e:
        raise Exception(
            "Could not parse http.post result, most likely because of a server side error or incorrect url.")


def put(path):
    """Perform an http.put"""
    global headers
    if logged_in:
        r = requests.put(config['aquarium_url'] + path, headers=headers)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return r.json()
    except Exception as e:
        raise Exception(
            "Could not parse http.post result, most likely because of a server side error or incorrect url.")


def post(path, data):
    """Perform an http.post"""
    global headers
    if logged_in:
        r = requests.post(config['aquarium_url'] +
                          path, json=data, headers=headers)
    else:
        raise Exception(
            "Not logged into an Aquarium instance. Run aq.login().")

    try:
        return r.json()
    except Exception as e:
        raise Exception(
            "Could not parse http.post result, most likely because of a server side error or incorrect url.")


def __fix_remember_token(h):
    """Reformat the remember token from rails, which may have extra characters in its name"""
    parts = h.split(';')
    rtok = ""
    for c in parts:
        cparts = c.split('=')
        if re.match('remember_token', cparts[0]):
            rtok = cparts[1]
    return "remember_token=" + rtok + "; " + h
