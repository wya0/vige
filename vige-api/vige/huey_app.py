"""
Huey entrypoint.

import all tasks in this file.

Run the consumer: `huey_consumer vige.huey_app.huey`
"""
from vige.huey_config import huey, logger  # noqa
# import all huey tasks here
from vige.api.wechat import tasks

@huey.task()
def echo(what):
    logger.info(what)
    return what
