# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.tenancy.models import Tenant, TenantGroup

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

OPTIONAL_ASSOCS = {"group": (TenantGroup, "name")}


class TenantInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            for assoc, details in OPTIONAL_ASSOCS.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            matching_params, defaults = self.split_params(params)
            tenant, created = Tenant.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("👩‍💻 Created Tenant", tenant.name)

            self.set_custom_fields_values(tenant, custom_field_data)
            self.set_tags(tenant, tags)


register_initializer("tenants", TenantInitializer)
