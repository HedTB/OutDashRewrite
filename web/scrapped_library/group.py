## -- IMPORTING -- ##

import typing

from flask import Flask

## -- VARIABLES -- ##

## -- FUNCTIONS -- ##

## -- CLASSES -- ##


class Group:
    app: Flask

    def __init__(self, app: Flask, *, route: str, method: typing.Callable, **options) -> None:
        self.app = app
        self.groups = []

        self._route = route
        self._options = options

        self.app.add_url_rule(route, view_func=method, **options)

    def route(self, route: str, **options):
        def decorated_function(method: typing.Callable):
            self.app.add_url_rule(f"{self._route}{route}", view_func=method, **options)
            return method

        return decorated_function

    def group(self, route: str, **options):
        def decorated_function(method: typing.Callable):
            self.groups.append(Group(self.app, route=f"{self._route}{route}", method=method, **options))
            return method

        return decorated_function
