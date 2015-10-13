from handlers import root, websocket


route_map = (
    ('GET', '/', root),
    ('GET', '/ws', websocket)
)
