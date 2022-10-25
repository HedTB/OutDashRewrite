## -- IMPORTS -- ##

import json
import logging
import os
from time import time

from jwcrypto import jwe, jwk

from utils.data import ApiUser, ApiUserData

## -- VARIABLES -- ##

secret = os.environ.get("SECRET")

logger = logging.getLogger("App")

## -- FUNCTIONS -- ##


def validate_user_token(token: str) -> tuple[int, dict | None, ApiUser | None]:
    start = time()

    try:
        key = jwk.JWK.from_password(secret)
        decrypted = jwe.JWE()

        decrypted.deserialize(raw_jwe=token, key=key)

        print(f"[validate] Loaded JWE, took: {(time() - start) * 1000} ms")
        start = time()

        data = json.loads(decrypted.payload)

        user_data_obj = ApiUserData(
            user_id=data["sub"],
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=data["exp"],
        )

        print(f"[validate] Created API user data, took: {(time() - start) * 1000} ms")
        print()

        return 200, data, user_data_obj

    except jwe.InvalidJWEData:
        return 401, None, None
    except Exception as error:
        logger.exception(error)
        return 400, None, None
