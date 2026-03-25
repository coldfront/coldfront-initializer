# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Resource, ResourceType
from coldfront.tenancy.models import Tenant

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

OPTIONAL_ASSOCS = {
    "resource_type": (ResourceType, "name"),
    "tenant": (Tenant, "name"),
}


class ResourceInitializer(BaseInitializer):
    data_file_name = "resources.yml"

    def load_data(self):
        resources = self.load_yaml()
        if resources is None:
            return

        for params in resources:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            for assoc, details in OPTIONAL_ASSOCS.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            matching_params, defaults = self.split_params(params)
            resource, created = Resource.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created resource", resource.name)

            self.set_custom_fields_values(resource, custom_field_data)
            self.set_tags(resource, tags)


register_initializer("resources", ResourceInitializer)
