import os
import pickle

from . import settings


def get_followers(api, user_id, limit=None):
    user_followers_pks = []
    uuid = api.generate_uuid()
    user_followers_response = api.user_followers(user_id, uuid)
    user_followers_pks.extend(map(lambda user: user["pk"], user_followers_response["users"]))

    while "big_list" in user_followers_response \
            and user_followers_response["big_list"] \
            and "next_max_id" in user_followers_response \
            and (limit is None or len(user_followers_pks) < limit):
        next_max_id = user_followers_response["next_max_id"]
        user_followers_response = api.user_followers(user_id, uuid, max_id=next_max_id)
        user_followers_pks.extend(map(lambda user: user["pk"], user_followers_response["users"]))

    return user_followers_pks


def get_following(api, user_id, limit=None):
    user_following_pks = []
    uuid = api.generate_uuid()
    user_following_response = api.user_following(user_id, uuid)
    user_following_pks.extend(map(lambda user: user["pk"], user_following_response["users"]))

    while "big_list" in user_following_response \
            and user_following_response["big_list"] \
            and "next_max_id" in user_following_response \
            and (limit is None or len(user_following_pks) < limit):
        next_max_id = user_following_response["next_max_id"]
        user_following_response = api.user_following(user_id, uuid, max_id=next_max_id)
        user_following_pks.extend(map(lambda user: user["pk"], user_following_response["users"]))

    return user_following_pks


def get_ignore_state(api):
    if os.path.exists(settings.INITIAL_STATE_PATH):
        with open(settings.INITIAL_STATE_PATH, "rb") as f:
            state = pickle.load(f)
    else:
        my_id = api.current_user()["user"]["pk"]

        followers, following = get_followers(api, my_id), get_following(api, my_id)

        state = {
            "followers": list(followers),
            "following": list(following),
        }

        with open(settings.INITIAL_STATE_PATH, "wb") as f:
            pickle.dump(state, f)

    return state
