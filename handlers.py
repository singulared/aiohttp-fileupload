import aiohttp_jinja2
import asyncio
from aiohttp import web
import aiohttp
from aiohttp import websocket


@aiohttp_jinja2.template('root.html')
async def root(request):
    return {}

callbacks = []

def callback_factory(ws, request):
    def callback(readed, out, ws=ws, request=request):
        if out is request._reader.output:
            ws.send_str('{}'.format(readed))
    return callback


async def websocket(request):
    ws = web.WebSocketResponse()
    ws.start(request)

    callbacks.append(callback_factory(ws, request))

    while not ws.closed:
        msg = await ws.receive()
        print(msg.extra)

        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                ws.send_str(msg.data + '/answer')
        elif msg.tp == aiohttp.MsgType.close:
            print('websocket connection closed')
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())
        elif msg.tp == aiohttp.MsgType.binary:
            print(msg.tp, dir(msg))
            with open('test', 'wb') as file:
                file.write(msg.data)

    return ws
