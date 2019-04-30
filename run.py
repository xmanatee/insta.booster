from instagram_private_api import Client
import logging
import time
import traceback
import argparse

from app.orm_schema import *
from app import settings
from app.crawler import crawl
from app.follower import (
    follow_worthy,
    accept_new_followers,
    unfollow_unworthy,
)
# from instabooster.utils import get_ignore_state
# https://instagram-private-api.readthedocs.io/en/latest/api.html


def one_iter(api, orm):

    crawl(api, orm, num_iter=10)
    follow_worthy(api, orm, num_iter=5)
    accept_new_followers(api, orm)
    unfollow_unworthy(api, orm, num_iter=20)

    time.sleep(settings.ITER_DELAY_SECONDS)


parser = argparse.ArgumentParser(description='Run Instagram Booster.')
parser.add_argument('--username', required=True, help='Instagram username')
parser.add_argument('--password', required=True, help='Instagram password')

if __name__ == "__main__":
    # logging.setLoggerClass(logging.getLogger('InstaBooster'))
    logging.basicConfig(level=logging.INFO)
    args = parser.parse_args()

    orm = get_session(settings.ORM_PATH)
    api = Client(args.username, args.password)

    # ignore_state = get_ignore_state(api)

    current = orm.query(QueueUserId).filter_by(processed_on=None).first()
    if not current:
        me = api.current_user()["user"]
        logging.info("Initializing queue with me : {}".format(me["username"]))
        record = {
            "id": me["pk"],
        }
        orm.add(QueueUserId(**record))
        orm.commit()

    for _ in range(10000):
        try:
            logging.info("")
            logging.info("===== NEXT ITERATION =====")
            logging.makeLogRecord({
                "queue": orm.query(QueueUserId).count(),
                "follows": orm.query(InstaFollow).count(),
                "users": orm.query(InstaUser).count(),
                "worthy": orm.query(WorthyUserId).count(),
            })
            logging.info("Queue size : {}".format(orm.query(QueueUserId).count()))
            logging.info("Follows size : {}".format(orm.query(InstaFollow).count()))
            logging.info("Users size : {}".format(orm.query(InstaUser).count()))
            logging.info("Worthy size: {}".format(orm.query(WorthyUserId).count()))

            one_iter(api, orm)

            time.sleep(settings.ITER_DELAY_SECONDS)

        except Exception as e:
            traceback.print_tb(e.__traceback__)
            logging.error("Exception occured: {}".format(e))
            logging.error("Reinitializing API...")
            time.sleep(settings.API_RESET_DELAY_SECONDS)
            orm = get_session(settings.ORM_PATH)
            # api = Client(args.username, args.password)
