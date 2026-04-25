from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def valid_gateway():
    return MagicMock(name="gateway")


def test_get_gateway_validates_settings_and_configures_boa_once(valid_gateway):
    from django_arc_monitize_api import logic
    from django_arc_monitize_api.conf import arc_settings

    with (
        patch.object(arc_settings, "check") as mock_check,
        patch("django_arc_monitize_api.logic.boa.set_network_env") as mock_rpc,
        patch(
            "django_arc_monitize_api.logic.create_gateway_middleware",
            return_value=valid_gateway,
        ) as mock_create,
    ):
        g1 = logic.get_gateway()
        g2 = logic.get_gateway()

    assert g1 is valid_gateway is g2
    mock_check.assert_called_once()
    mock_rpc.assert_called_once_with(arc_settings.ARC_RPC_URL)
    mock_create.assert_called_once_with(
        seller_address=arc_settings.SELLER_ADDRESS,
        chain=arc_settings.NETWORK,
    )


def test_get_gateway_raises_when_settings_invalid():
    from django_arc_monitize_api import logic
    from django_arc_monitize_api.conf import arc_settings

    with (
        patch.object(
            arc_settings,
            "check",
            side_effect=ImproperlyConfigured("missing ARC_PAY_SELLER_ADDRESS"),
        ),
        patch("django_arc_monitize_api.logic.boa.set_network_env") as mock_rpc,
        patch("django_arc_monitize_api.logic.create_gateway_middleware") as mock_create,
    ):
        with pytest.raises(ImproperlyConfigured, match="missing"):
            logic.get_gateway()

    mock_rpc.assert_not_called()
    mock_create.assert_not_called()
    assert logic._gateway is None
