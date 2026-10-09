from starlette.datastructures import Headers
from starlette.middleware.gzip import GZipMiddleware, GZipResponder
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SSEAwareGZipResponder(GZipResponder):
    """Keep event streams uncompressed so their chunks reach clients immediately."""

    def __init__(self, app: ASGIApp, minimum_size: int, compresslevel: int = 9) -> None:
        super().__init__(app, minimum_size, compresslevel=compresslevel)
        self._sse = False

    async def send_with_gzip(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            content_type = Headers(raw=message["headers"]).get("content-type", "")
            if content_type.lower().startswith("text/event-stream"):
                self._sse = True
                await self.send(message)
                return
        if self._sse:
            await self.send(message)
            return
        await super().send_with_gzip(message)


class SSEAwareGZip(GZipMiddleware):
    """Apply gzip to normal responses without buffering server-sent events."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope.get("path", "").endswith("/stream"):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        if "gzip" in headers.get("Accept-Encoding", ""):
            responder: ASGIApp = SSEAwareGZipResponder(self.app, self.minimum_size, compresslevel=self.compresslevel)
            await responder(scope, receive, send)
            return
        await self.app(scope, receive, send)
