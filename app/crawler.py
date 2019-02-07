import logging
import time
from datetime import datetime

from . import settings
from .orm_schema import *


def crawl(api, orm, num_iter=None):
    current = orm.query(QueueUserId).filter_by(processed_on=None).first()
    # print(current, current.id)

    cur_iter = 0
    while current and (num_iter is None or cur_iter < num_iter):
        current_info = api.user_info(current.id)["user"]
        # putting user to DB
        logging.info("processing {}".format(current_info["username"]))
        record = {
            "id": current_info["pk"],
            "user_name": current_info["username"],
            "full_name": current_info["full_name"],
            "followers_count": current_info["follower_count"],
            "following_count": current_info["following_count"],
            "media_count": current_info["media_count"],
        }
        orm.add(InstaUser(**record))

        # get new users
        uuid = api.generate_uuid()
        following_users = api.user_followers(current.id, uuid)["users"]
        for following_user in following_users:
            following_user_id = following_user["pk"]
            if not orm.query(QueueUserId).filter_by(id=following_user_id).first():
                orm.add(QueueUserId(id=following_user_id))
            if not orm.query(InstaFollow).filter_by(from_id=following_user_id, to_id=current.id).first():
                orm.add(InstaFollow(from_id=following_user_id, to_id=current.id))

        # update processed_on
        current.processed_on = datetime.now()

        # commiting changes
        orm.commit()

        #search step
        current = orm.query(QueueUserId).filter_by(processed_on=None).first()

        time.sleep(settings.DEFAULT_DELAY)
        cur_iter += 1
