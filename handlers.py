import aiohttp_jinja2
import asyncio
import aiohttp
import json
import tempfile
import os
from hashlib import md5
from time import localtime


callbacks = []


@aiohttp_jinja2.template('root.html')
async def root(request):
    return {}


def save_file(data, filename):
    with open(os.path.join('uploads', filename), 'wb') as file:
        file.write(data)
    return '/uploads/{}'.format(filename)


def callback_factory(ws, request):
    def send_progress_callback(received, out, ws=ws, request=request):
        if out is request._reader.output:
            ws.send_str(json.dumps({'received': received,
                                    'state': 'uploading'}))
    return send_progress_callback


async def websocket(request):
    ws = aiohttp.web.WebSocketResponse()
    ws.start(request)

    callback = callback_factory(ws, request)
    callbacks.append(callback)
    loop = asyncio.get_event_loop()
    filename = md5(str(localtime()).encode()).hexdigest()

    while not ws.closed:
        msg = await ws.receive()

        if msg.tp == aiohttp.MsgType.text:
            if msg.data == 'close':
                await ws.close()
            else:
                metadata = json.loads(msg.data)
                if 'filename' in metadata:
                    filename = metadata['filename']
                request.app.logger.info('upload request - {} {} bytes'.format(
                    metadata.get('filename', filename),
                    metadata.get('size', '')))

        elif msg.tp == aiohttp.MsgType.close:
            print('websocket connection closed')
            callbacks.remove(callback)
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s' %
                  ws.exception())
            callbacks.remove(callback)
        elif msg.tp == aiohttp.MsgType.binary:
            url = await loop.run_in_executor(None, save_file, msg.data,
                                             filename)
            ws.send_str(json.dumps({'received': len(msg.data),
                                    'state': 'done',
                                    'url': url}))
    return ws
