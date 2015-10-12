import asyncio
import io
from aiohttp.web_reqrep import FileField
from aiohttp.web import Response
from types import MethodType
import settings
import json


REQUEST_FIELD_NAME = 'file_fields'


class BufferedRandomCallback(io.BufferedRandom):
    def __init__(self, file, request, callback, size):
        self._io = file
        self.request = request
        self.callback = callback
        self.size = size
        self.load_id = request.GET['X-Progress-ID']

    def read(self):
        chunk = True
        data = b''
        while chunk:
            chunk = self._io.read(settings.uploadprogress_step)
            data += chunk
            self.callback(self.request.app, self.load_id, len(data), self.size)
            import time
        return data


def callback(app, id, received, size):
    if received < size:
        state = 'uploading'
    else:
        state = 'done'
    app.upload_progress[id] = {'recived': received,
                               'size': size,
                               'state': state}
    print('callback on {} {}/{}'.format(id, received, size))


async def register_upload(request):
    data = await request.post()
    request[REQUEST_FIELD_NAME] = []
    for key, value in data.items():
        if hasattr(value, 'filename'):
            size = value.file.seek(0, io.SEEK_END)
            value.file.seek(0)
            request[REQUEST_FIELD_NAME].append(
                FileField(
                    name=value.name,
                    filename=value.filename,
                    file=BufferedRandomCallback(value.file, request, callback,
                                                size),
                    content_type=value.content_type
                )
            )


async def return_state(request):
    try:
        state = request.app.upload_progress[request.GET['X-Progress-ID']]
    except KeyError:
        state = {}
    return Response(body=json.dumps(state).encode())


async def upload_progress_middleware(app, handler):
    if not hasattr(app, 'upload_progress'):
        app.upload_progress = {}
    async def middleware(request):
        # register upload
        if 'X-Progress-ID' in request.GET:
            if request.method == 'POST':
                await register_upload(request)
            elif request.method == 'GET':
                return await return_state(request)
        return await handler(request)
    return middleware
