import logging
import time
from datetime import datetime, timedelta

from . import settings
from .orm_schema import *


def worth_following(followers_count, following_count, media_count):
    return (
        following_count > 100
        and followers_count / following_count < 1.2
    )


class Status:
    FOLLOWED = 1
    FAILED = 2
    SUCCEEDED = 3


def follow_worthy(api, orm, num_iter=None):
    all_users = orm.query(InstaUser). \
        outerjoin(WorthyUserId, InstaUser.id == WorthyUserId.id). \
        filter(WorthyUserId.id == None). \
        all()

    worthy_users = list(
        filter(
            lambda user: worth_following(user.followers_count, user.following_count, user.media_count),
            all_users
        )
    )

    if num_iter is not None:
        worthy_users = worthy_users[:num_iter]

    for worthy_user in worthy_users:
        r = api.friendships_create(worthy_user.id)
        logging.info("following {}: {}".format(worthy_user.id, r["status"]))
        r = api.friendships_show(worthy_user.id)
        # logging.info("cur_status {}: {}".format(worthy_user.id, r))
        orm.add(WorthyUserId(id=worthy_user.id, status=Status.FOLLOWED))
        orm.commit()

        time.sleep(settings.DEFAULT_DELAY)


def accept_new_followers(api, orm):
    pass


def unfollow_unworthy(api, orm, num_iter=None):
    followed_users = orm.query(WorthyUserId).filter_by(status=Status.FOLLOWED).all()

    users_to_unfollow = list(
        filter(
            lambda user: datetime.now() - user.added_on > timedelta(days=settings.FOLLOW_DAYS_PERIOD),
            followed_users
        )
    )

    if num_iter is not None:
        users_to_unfollow = users_to_unfollow[:num_iter]

    for user_to_unfollow in users_to_unfollow:
        follow_status = api.friendships_show(user_to_unfollow.id)

        logging.info("unfollowing {}".format(user_to_unfollow.id))

        api.friendships_destroy(user_to_unfollow.id)

        if follow_status["followed_by"] or follow_status["incoming_request"]:
            user_to_unfollow.status = Status.SUCCEEDED
        else:
            user_to_unfollow.status = Status.FAILED

        orm.commit()
        time.sleep(settings.DEFAULT_DELAY)
