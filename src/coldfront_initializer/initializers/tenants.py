# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.tenancy.models import Tenant, TenantGroup

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class TenantInitializer(BaseInitializer):
    MODEL = Tenant
    OPTIONAL_ASSOCS = {"group": (TenantGroup, "name")}


register_initializer("tenants", TenantInitializer)
