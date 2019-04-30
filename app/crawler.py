import logging
import time
import json
from datetime import datetime
from sqlalchemy.sql.expression import func

from . import settings
from .orm_schema import *
from .utils import get_followers


def crawl(api, orm, num_iter=None):
    current = orm.query(QueueUserId).filter_by(processed_on=None).order_by(func.random()).first()

    cur_iter = 0
    while current and (num_iter is None or cur_iter < num_iter):
        current_info = api.user_info(current.id)["user"]
        # putting user to DB
        logging.info("crawling {}".format(current_info["username"]))
        record = {
            "id": current_info["pk"],
            "username": current_info["username"],
            "full_name": current_info["full_name"],
            "followers_count": current_info["follower_count"],
            "following_count": current_info["following_count"],
            "media_count": current_info["media_count"],
            "info_json": json.dumps(current_info),
        }
        orm.add(InstaUser(**record))

        # get new users
        following_user_ids = get_followers(api, current.id, settings.MAX_FOLLOWERS_CRAWLED)
        for following_user_id in following_user_ids:
            if not orm.query(QueueUserId).filter_by(id=following_user_id).first():
                orm.add(QueueUserId(id=following_user_id))
            if not orm.query(InstaFollow).filter_by(from_id=following_user_id, to_id=current.id).first():
                orm.add(InstaFollow(from_id=following_user_id, to_id=current.id))

        # update processed_on
        current.processed_on = datetime.now()

        # commiting changes
        orm.commit()

        # search step
        current = orm.query(QueueUserId).filter_by(processed_on=None).first()

        time.sleep(settings.DEFAULT_DELAY_SECONDS)
        cur_iter += 1
