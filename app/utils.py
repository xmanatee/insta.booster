import os
import pickle

from . import settings


def get_followers_following(api, user_id):

    uuid = api.generate_uuid()
    followers = map(
        lambda user: user["pk"],
        api.user_followers(user_id, uuid)["users"]
    )

    uuid = api.generate_uuid()
    following = map(
        lambda user: user["pk"],
        api.user_following(user_id, uuid)["users"]
    )

    return followers, following


def get_ignore_state(api):
    if os.path.exists(settings.INITIAL_STATE_PATH):
        with open(settings.INITIAL_STATE_PATH, "rb") as f:
            state = pickle.load(f)
    else:
        my_id = api.current_user()["user"]["pk"]

        followers, following = get_followers_following(api, my_id)

        state = {
            "followers": list(followers),
            "following": list(following),
        }

        with open(settings.INITIAL_STATE_PATH, "wb") as f:
            pickle.dump(state, f)

    return state
