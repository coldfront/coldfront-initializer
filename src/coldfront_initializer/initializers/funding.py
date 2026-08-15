# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging
from decimal import Decimal

from coldfront.models.utils import get_default_currency
from coldfront.ras.models import Project
from coldfront.ris.models import Funding
from coldfront.users.models import User
from djmoney.money import Money

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class FundingInitializer(BaseInitializer):
    MODEL = Funding
    OPTIONAL_ASSOCS = {
        "created_by": (User, "username"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "projects": (Project, "slug"),
    }
    # (award_number, funding_agency) is the canonical identity of a funding
    # record (mirrors the model's unique_together constraint).
    MATCH_PARAMS = ["award_number", "funding_agency"]

    def _pre_process(self, params):
        # Convert the YAML money value into a djmoney ``Money`` instance so it
        # is stored correctly by the MoneyField. Accepts a bare amount
        # ("1000000.00", using the default currency) or an amount plus a
        # currency code ("1000000.00 USD"), matching ColdFront's CSV import.
        value = params.pop("amount_awarded", None)
        if value is None or value == "" or value == "null":
            params["amount_awarded"] = None
            return
        if isinstance(value, Money):
            params["amount_awarded"] = value
            return
        if isinstance(value, str):
            value = value.strip()
            if " " in value:
                amount, currency = value.rsplit(" ", 1)
            else:
                amount, currency = value, get_default_currency()
            params["amount_awarded"] = Money(Decimal(amount), currency)
        else:
            params["amount_awarded"] = Money(Decimal(value), get_default_currency())


register_initializer("funding", FundingInitializer)
