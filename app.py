import settings
import os
import logging

if settings.debug:
    os.environ['PYTHONASYNCIODEBUG'] = '1'

import aiohttp.websocket
aiohttp.websocket._do_handshake = aiohttp.websocket.do_handshake

def do_handshake_hacked(method, headers, transport, protocols=()):
    params = list(aiohttp.websocket._do_handshake(
        method, headers, transport, protocols))
    import wsparser
    params[2] = wsparser.WebSocketHackedParser
    return tuple(params)

aiohttp.websocket.do_handshake = do_handshake_hacked

import asyncio
from aiohttp import web
from urls import route_map
import jinja2
import aiohttp_jinja2


if settings.debug:
    logging.getLogger('asyncio').setLevel(logging.DEBUG)


def app_factory():
    app = web.Application()

    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('templates'))

    app.logger = logging.getLogger('')
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
