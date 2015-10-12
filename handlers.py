import aiohttp_jinja2
import asyncio


@aiohttp_jinja2.template('root.html')
async def root(request):
    return {}


def save_files(files):
    urls = []
    for file_field in files:
        with open('uploads/{}'.format(file_field.filename), 'wb') as file:
            file.write(file_field.file.read())
            urls.append('/uploads/{}'.format(file_field.filename))
    return urls


@aiohttp_jinja2.template('root.html')
async def upload(request):
    data = await request.post()
    #import ipdb; ipdb.set_trace()  # XXX BREAKPOINT
    files = request['file_fields']
    loop = asyncio.get_event_loop()
    urls = await loop.run_in_executor(None, save_files, files)
    return {'urls': urls}
