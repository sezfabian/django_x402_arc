import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from django.http import JsonResponse
from django.test import AsyncRequestFactory, RequestFactory

from django_arc_monitize_api.decorators import monetize


def test_monetize_sync_uses_async_to_sync():
    factory = RequestFactory()
    request = factory.get("/api/premium/")
    gw = MagicMock()
    gw.process_request = AsyncMock(
        return_value={
            "status": 402,
            "body": {"detail": "pay"},
            "headers": {"PAYMENT-REQUIRED": "req"},
        }
    )

    @monetize("0.01")
    def view(r):
        return JsonResponse({"paid": True})

    with patch("django_arc_monitize_api.decorators.get_gateway", return_value=gw):
        response = view(request)

    assert response.status_code == 402
    gw.process_request.assert_called_once()
    assert response["PAYMENT-REQUIRED"] == "req"


def test_monetize_async_awaits_process_request():
    factory = AsyncRequestFactory()
    request = factory.get("/api/premium/")
    gw = MagicMock()
    gw.process_request = AsyncMock(
        return_value={
            "status": 402,
            "body": {"detail": "pay"},
            "headers": {"PAYMENT-REQUIRED": "req"},
        }
    )

    @monetize("0.01")
    async def view(r):
        return JsonResponse({"paid": True})

    async def run():
        with patch("django_arc_monitize_api.decorators.get_gateway", return_value=gw):
            return await view(request)

    response = asyncio.run(run())
    assert response.status_code == 402
    gw.process_request.assert_awaited_once()
    assert response["PAYMENT-REQUIRED"] == "req"
