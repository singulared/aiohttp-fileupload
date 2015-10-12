import aiohttp_jinja2


@aiohttp_jinja2.template('root.html')
async def root(request):
    return {}


@aiohttp_jinja2.template('root.html')
async def upload(request):
    return {}
