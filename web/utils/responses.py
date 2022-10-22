## -- IMPORTING -- ##

from flask import request

## -- VARIABLES -- ##

## -- FUNCTIONS -- ##

def invalid_user_token():
    return {"message": "Invalid user token, please re-login", "error": "invalid_token"}, 401

def invalid_access_token():
    return {"message": "Invalid access token, please re-login", "error": "invalid_access_token"}
