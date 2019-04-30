import logging
import random
import time
import traceback
from datetime import datetime, timedelta

from . import settings
from .orm_schema import *


def worthiness(user):
    if user.following_count < 100:
        return -1

    if user.followers_count < 1:
        return 1

    return user.following_count / user.followers_count


def worth_following(user):
    return worthiness(user) > 0.8


class Status:
    FOLLOWED = 1
    FAILED = 2
    SUCCEEDED = 3
    IRRELEVANT = 4


def pretty_status(json_status):
    return " ".join(item[0] for item in json_status.items() if item[1])


def follow_worthy(api, orm, num_iter=None):
    all_users = orm.query(InstaUser). \
        outerjoin(WorthyUserId, InstaUser.id == WorthyUserId.id). \
        filter(WorthyUserId.id == None). \
        all()

    # worthy_users = filter(lambda user: worth_following(user), all_users)
    worthy_users = sorted(all_users, key=worthiness, reverse=True)

    if num_iter is not None:
        worthy_users = worthy_users[:num_iter * 2]
        random.shuffle(worthy_users)
        worthy_users = worthy_users[:num_iter]

    for worthy_user in worthy_users:
        friendship_status = api.friendships_show(worthy_user.id)
        if friendship_status["incoming_request"] \
                or friendship_status["followed_by"] \
                or friendship_status["outgoing_request"] \
                or friendship_status["following"]:
            logging.info(
                "skipping {} with status {}".format(
                    worthy_user.username,
                    pretty_status(friendship_status)))
            orm.add(WorthyUserId(id=worthy_user.id, status=Status.IRRELEVANT))
            orm.commit()
            continue
        like_some_posts(api, worthy_user)

        friendship_request = api.friendships_create(worthy_user.id)
        friendship_status = api.friendships_show(worthy_user.id)
        logging.info(
            "followed {} (worthiness={}) with status {}".format(
                worthy_user.username,
                worthiness(worthy_user),
                pretty_status(friendship_status)))
        orm.add(WorthyUserId(id=worthy_user.id, status=Status.FOLLOWED))
        orm.commit()

        time.sleep(settings.DEFAULT_DELAY_SECONDS)


def like_some_posts(api, user):
    try:
        user_feed = api.user_feed(user.id)
        user_feed_ids = [(post['like_count'], post['id']) for post in user_feed['items'][:5]]

        user_media_ids_to_like = {
            min(user_feed_ids)[1],
            max(user_feed_ids)[1]
        }
        for user_media_id_to_like in user_media_ids_to_like:
            like_status = api.post_like(user_media_id_to_like, module_name='feed_timeline')
            logging.info(
                "liked {} with status {}".format(
                    user.username,
                    pretty_status(like_status)))

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        logging.error("Exception occured when liking: {}".format(e))
        time.sleep(settings.LIKE_FAILURE_DELAY_SECONDS)


def accept_new_followers(api, orm):
    pass


def unfollow_unworthy(api, orm, num_iter=None):
    followed_users = orm.query(WorthyUserId).filter_by(status=Status.FOLLOWED).all()

    users_to_unfollow = list(
        filter(
            lambda user: datetime.now() - user.added_on > timedelta(days=settings.FOLLOW_PERIOD_DAYS),
            followed_users))

    if num_iter is not None:
        users_to_unfollow = users_to_unfollow[:num_iter]

    for user_to_unfollow in users_to_unfollow:
        follow_status = api.friendships_show(user_to_unfollow.id)

        logging.info("unfollowing {} with status".format(user_to_unfollow.id, follow_status))

        api.friendships_destroy(user_to_unfollow.id)

        if follow_status["followed_by"] or follow_status["incoming_request"]:
            user_to_unfollow.status = Status.SUCCEEDED
        else:
            user_to_unfollow.status = Status.FAILED

        orm.commit()
        time.sleep(settings.DEFAULT_DELAY_SECONDS)
