## -- IMPORTING -- ##

import typing

from flask import Flask

from .group import Group

## -- VARIABLES -- ##

## -- FUNCTIONS -- ##

## -- CLASSES -- ##


class App:
    app: Flask

    def __init__(self, app: Flask) -> None:
        self.app = app
        self.groups = []

    def route(self, route: str, **options):
        def decorated_function(method: typing.Callable):
            self.app.add_url_rule(route, view_func=method, **options)
            return method

        return decorated_function

    def group(self, route: str, **options):
        def decorated_function(method: typing.Callable):
            self.groups.append(Group(self.app, route=route, method=method, **options))
            return method

        return decorated_function


## -- SETUP -- ##
