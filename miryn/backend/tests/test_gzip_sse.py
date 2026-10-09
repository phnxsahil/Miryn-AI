from app.core.gzip_sse import SSEAwareGZipResponder


def _run(coroutine):
    try:
        coroutine.send(None)
    except StopIteration:
        return


def test_sse_is_not_gzipped_but_large_json_is() -> None:
    async def send(message):
        messages.append(message)

    messages: list[dict] = []
    sse_responder = SSEAwareGZipResponder(lambda *_args: None, minimum_size=500)
    sse_responder.send = send
    _run(sse_responder.send_with_gzip({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"text/event-stream"]],
    }))
    _run(sse_responder.send_with_gzip({"type": "http.response.body", "body": b"data: ready\n\n"}))
    sse_headers = dict(messages[0]["headers"])
    assert b"content-encoding" not in sse_headers

    messages.clear()
    json_responder = SSEAwareGZipResponder(lambda *_args: None, minimum_size=500)
    json_responder.send = send
    _run(json_responder.send_with_gzip({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"application/json"]],
    }))
    _run(json_responder.send_with_gzip({"type": "http.response.body", "body": b"x" * 2048}))
    json_headers = dict(messages[0]["headers"])
    assert json_headers[b"content-encoding"] == b"gzip"
    assert b"accept-encoding" in json_headers[b"vary"].lower()
