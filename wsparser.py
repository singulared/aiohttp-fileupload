import aiohttp.websocket
aiohttp.websocket._do_handshake = aiohttp.websocket.do_handshake

def do_handshake_hacked(method, headers, transport, protocols=()):
    params = list(aiohttp.websocket._do_handshake(
        method, headers, transport, protocols))
    params[2] = WebSocketHackedParser
    return tuple(params)

aiohttp.websocket.do_handshake = do_handshake_hacked

from aiohttp.websocket import *
from aiohttp.websocket import (parse_frame, OPCODE_CLOSE, OPCODE_PING,
                               OPCODE_PONG, OPCODE_TEXT, OPCODE_BINARY,
                               OPCODE_CONTINUATION, UNPACK_CLOSE_CODE,
                               ALLOWED_CLOSE_CODES)
from handlers import callbacks


def WebSocketHackedParser(out, buf):
    while True:
        fin, opcode, payload = yield from parse_frame(buf)

        if opcode == OPCODE_CLOSE:
            if len(payload) >= 2:
                close_code = UNPACK_CLOSE_CODE(payload[:2])[0]
                if close_code not in ALLOWED_CLOSE_CODES and close_code < 3000:
                    raise WebSocketError(
                        CLOSE_PROTOCOL_ERROR,
                        'Invalid close code: {}'.format(close_code))
                try:
                    close_message = payload[2:].decode('utf-8')
                except UnicodeDecodeError as exc:
                    raise WebSocketError(
                        CLOSE_INVALID_TEXT,
                        'Invalid UTF-8 text message') from exc
                msg = Message(OPCODE_CLOSE, close_code, close_message)
            elif payload:
                raise WebSocketError(
                    CLOSE_PROTOCOL_ERROR,
                    'Invalid close frame: {} {} {!r}'.format(
                        fin, opcode, payload))
            else:
                msg = Message(OPCODE_CLOSE, 0, '')

            out.feed_data(msg, 0)

        elif opcode == OPCODE_PING:
            out.feed_data(Message(OPCODE_PING, payload, ''), len(payload))

        elif opcode == OPCODE_PONG:
            out.feed_data(Message(OPCODE_PONG, payload, ''), len(payload))

        elif opcode not in (OPCODE_TEXT, OPCODE_BINARY):
            raise WebSocketError(
                CLOSE_PROTOCOL_ERROR, "Unexpected opcode={!r}".format(opcode))
        else:
            # load text/binary
            data = [payload]

            while not fin:
                fin, _opcode, payload = yield from parse_frame(buf, True)

                # We can receive ping/close in the middle of
                # text message, Case 5.*
                if _opcode == OPCODE_PING:
                    out.feed_data(
                        Message(OPCODE_PING, payload, ''), len(payload))
                    fin, _opcode, payload = yield from parse_frame(buf, True)
                elif _opcode == OPCODE_CLOSE:
                    if len(payload) >= 2:
                        close_code = UNPACK_CLOSE_CODE(payload[:2])[0]
                        if (close_code not in ALLOWED_CLOSE_CODES and
                                close_code < 3000):
                            raise WebSocketError(
                                CLOSE_PROTOCOL_ERROR,
                                'Invalid close code: {}'.format(close_code))
                        try:
                            close_message = payload[2:].decode('utf-8')
                        except UnicodeDecodeError as exc:
                            raise WebSocketError(
                                CLOSE_INVALID_TEXT,
                                'Invalid UTF-8 text message') from exc
                        msg = Message(OPCODE_CLOSE, close_code, close_message)
                    elif payload:
                        raise WebSocketError(
                            CLOSE_PROTOCOL_ERROR,
                            'Invalid close frame: {} {} {!r}'.format(
                                fin, opcode, payload))
                    else:
                        msg = Message(OPCODE_CLOSE, 0, '')

                    out.feed_data(msg, 0)
                    fin, _opcode, payload = yield from parse_frame(buf, True)

                if _opcode != OPCODE_CONTINUATION:
                    raise WebSocketError(
                        CLOSE_PROTOCOL_ERROR,
                        'The opcode in non-fin frame is expected '
                        'to be zero, got {!r}'.format(_opcode))
                else:
                    data.append(payload)
                    data_length = sum(map(len, data))
                    for callback in callbacks:
                        callback(data_length, out=out)

            if opcode == OPCODE_TEXT:
                try:
                    text = b''.join(data).decode('utf-8')
                    out.feed_data(
                        Message(
                            OPCODE_TEXT, text, ''), len(text))
                except UnicodeDecodeError as exc:
                    raise WebSocketError(
                        CLOSE_INVALID_TEXT,
                        'Invalid UTF-8 text message') from exc
            else:
                data = b''.join(data)
                out.feed_data(
                    Message(OPCODE_BINARY, data, ''), len(data))
