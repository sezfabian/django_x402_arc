from functools import wraps
from inspect import iscoroutinefunction

from asgiref.sync import async_to_sync
from django.http import JsonResponse

from .logic import get_gateway


def _payment_required_response(result: dict) -> JsonResponse:
    status = result.get("status", 402)
    response = JsonResponse(result["body"], status=status)
    for k, v in result.get("headers", {}).items():
        response[k] = v
    return response


def monetize(price_usdc: str):
    """
    Decorator to wrap any Django view with an x402 USDC paywall.
    Use with async views (recommended): ``@monetize("0.005")`` on ``async def``.
    Sync views are supported via ``async_to_sync`` for the gateway call.
    """
    def decorator(view_func):
        if iscoroutinefunction(view_func):

            @wraps(view_func)
            async def _wrapped_async(request, *args, **kwargs):
                gw = get_gateway()
                payment_sig = request.headers.get("PAYMENT-SIGNATURE")
                result = await gw.process_request(
                    payment_header=payment_sig,
                    path=request.path,
                    price=price_usdc,
                )
                if isinstance(result, dict):
                    return _payment_required_response(result)
                request.payer = result.payer
                response = await view_func(request, *args, **kwargs)
                for k, v in result.response_headers.items():
                    response[k] = v
                return response

            return _wrapped_async

        @wraps(view_func)
        def _wrapped_sync(request, *args, **kwargs):
            gw = get_gateway()
            payment_sig = request.headers.get("PAYMENT-SIGNATURE")
            result = async_to_sync(gw.process_request)(
                payment_header=payment_sig,
                path=request.path,
                price=price_usdc,
            )
            if isinstance(result, dict):
                return _payment_required_response(result)
            request.payer = result.payer
            response = view_func(request, *args, **kwargs)
            for k, v in result.response_headers.items():
                response[k] = v
            return response

        return _wrapped_sync

    return decorator
