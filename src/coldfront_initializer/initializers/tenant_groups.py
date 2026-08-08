# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.tenancy.models import TenantGroup

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class TenantGroupInitializer(BaseInitializer):
    MODEL = TenantGroup
    OPTIONAL_ASSOCS = {"parent": (TenantGroup, "name")}


register_initializer("tenant_groups", TenantGroupInitializer)
