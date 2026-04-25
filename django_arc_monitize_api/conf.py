from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

class ArcPaySettings:
    @property
    def SELLER_ADDRESS(self):
        return getattr(settings, "ARC_PAY_SELLER_ADDRESS", None)

    @property
    def NETWORK(self):
        return getattr(settings, "ARC_PAY_NETWORK", "arcTestnet")

    @property
    def CIRCLE_API_KEY(self):
        return getattr(settings, "CIRCLE_API_KEY", None)

    @property
    def CIRCLE_ENTITY_SECRET(self):
        return getattr(settings, "CIRCLE_ENTITY_SECRET", None)

    @property
    def ARC_RPC_URL(self):
        return getattr(settings, "ARC_RPC_URL", "https://arc-testnet.drpc.org")

    @property
    def ARC_CHAIN_ID(self):
        return getattr(settings, "ARC_CHAIN_ID", 5042002)

    def check(self):
        required = ["ARC_PAY_SELLER_ADDRESS", "CIRCLE_API_KEY", "CIRCLE_ENTITY_SECRET"]
        for setting in required:
            if not getattr(settings, setting, None):
                raise ImproperlyConfigured(f"The setting {setting} is required for django-arc-pay.")

arc_settings = ArcPaySettings()
