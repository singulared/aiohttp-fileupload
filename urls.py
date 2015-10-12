from handlers import root, upload


route_map = (
    ('GET', '/', root),
    ('POST', '/upload', upload)
)
