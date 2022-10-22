## -- IMPORTING -- ##

## -- EXCEPTIONS -- ##


class InvalidUserToken(Exception):
    """Raised if the passed user token is invalid"""

    pass


class InvalidAccessToken(Exception):
    """Raised if the passed access/refresh token is invalid"""

    pass


class InvalidOauthCode(Exception):
    """Raised if the passed oauth code is invalid"""

    pass


## -- SETUP -- ##
