## -- IMPORTING -- ##

import json
import logging
import os
import time

from fastapi import APIRouter, Header, HTTPException, Body

from web.utils.models import VoteData


## -- VARIABLES -- ##

# CONSTANTS
API_KEY = os.environ.get("API_KEY")

# OBJECTS
router = APIRouter(prefix="/webhooks")
logger = logging.getLogger("App")

## -- FUNCTIONS -- ##

## -- MODELS -- ##


## -- ROUTES -- ##


@router.post(path="/bot-upvotes", include_in_schema=False)
async def bot_upvotes_webhook(vote_data: VoteData = Body(None), authorization: str = Header(default=None)):
    if authorization != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid authorization header")

    if vote_data.type == "test":
        print(vote_data)
    else:
        user_voted = vote_data.user
        is_weekend = vote_data.isWeekend

        print(f"User with ID {user_voted} has voted on top.gg.")

        with open("data/votes.json", "r") as file:
            file_data = json.load(file)

            file_data.update(
                {
                    str(user_voted): {
                        "is_weekend": is_weekend,
                        "expires_at": time.time() + (24 * 3600),
                    }
                }
            )
        with open("data/votes.json", "w") as file:
            json.dump(file_data, file)

    return {"message": "The vote has been logged"}
