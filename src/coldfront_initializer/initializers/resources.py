# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Resource, ResourceType
from coldfront.tenancy.models import Tenant
from coldfront.utils.jsonschema import validate_schema

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class ResourceInitializer(BaseInitializer):
    MODEL = Resource
    OPTIONAL_ASSOCS = {
        "resource_type": (ResourceType, "name"),
        "tenant": (Tenant, "name"),
        "parent": (Resource, "name"),
    }

    def _pre_process(self, params):
        if "schema" in params:
            validate_schema(params["schema"])


register_initializer("resources", ResourceInitializer)
