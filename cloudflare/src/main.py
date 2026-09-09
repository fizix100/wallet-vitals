from urllib.parse import urlsplit

from app import app
from workers import Response, WorkerEntrypoint, asgi


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if urlsplit(request.url).path in {
            "/wallet-vitals/demo.mp4", "/wallet-vitals/demo.vtt"
        }:
            # Serve through the asset binding without buffering video in ASGI.
            return await self.env.ASSETS.fetch(request)
        try:
            return await asgi.fetch(app, request, self.env, self.ctx)
        except Exception as exc:
            print("Request failed:", type(exc).__name__)
            return Response.from_json(
                {"detail": "Service temporarily unavailable. Please retry."}, status=503
            )
