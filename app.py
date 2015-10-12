import settings
import os
import logging

if settings.debug:
    os.environ['PYTHONASYNCIODEBUG'] = '1'

import asyncio
from aiohttp import web
from urls import route_map
import jinja2
import aiohttp_jinja2
from uploadprogress import upload_progress_middleware


if settings.debug:
    logging.getLogger('asyncio').setLevel(logging.DEBUG)


def app_factory():
    app = web.Application(middlewares=[upload_progress_middleware])

    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('templates'))

    app.logger = logging.getLogger('pandomim')
    ch = logging.StreamHandler()
    app.logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    app.logger.addHandler(ch)

    for route in route_map:
        app.router.add_route(*route)
    app.router.add_static('/uploads', 'uploads/', name='static')
    return app
