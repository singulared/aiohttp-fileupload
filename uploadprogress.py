

async def register_upload(request):
    data = await request.post()
    files = []
    for key, value in data.items():
        print(key, value)
        if getattr(value, 'filename', None):
            files.append(value)
    print(files)


async def upload_progress_middleware(app, handler):
    async def middleware(request):
        # register upload
        if 'X-Progress-ID' in request.GET and request.method == 'POST':
            await register_upload(request)
        return await handler(request)
    return middleware
