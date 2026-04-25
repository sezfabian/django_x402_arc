import django
import pytest
from django.conf import settings


def pytest_configure():
    if settings.configured:
        return
    settings.configure(
        SECRET_KEY="test-secret-key-for-pytest",
        USE_TZ=True,
        INSTALLED_APPS=[],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        ARC_PAY_SELLER_ADDRESS="0x1234567890123456789012345678901234567890",
        CIRCLE_API_KEY="test-circle-api-key",
        CIRCLE_ENTITY_SECRET="test-entity-secret",
        ARC_PAY_NETWORK="arcTestnet",
        ARC_RPC_URL="https://rpc.example.test",
    )
    django.setup()


@pytest.fixture(autouse=True)
def reset_logic_gateway():
    """Isolate tests that touch the lazy singleton in logic.get_gateway."""
    from django_arc_monitize_api import logic

    logic._gateway = None
    yield
    logic._gateway = None
