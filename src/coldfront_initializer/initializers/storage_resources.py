# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster, StorageResource

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

OPTIONAL_ASSOCS = {
    "tenant": ("tenancy.Tenant", "name"),
}


class StorageResourceInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            # Resolve M2M cluster references
            cluster_names = params.pop("clusters", None)

            # StorageResource has no slug field — discard if present
            params.pop("slug", None)

            matching_params, defaults = self.split_params(
                params, unique_params=["name"]
            )
            resource, created = StorageResource.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created StorageResource", resource.name)

            # Set M2M cluster associations after creation
            if cluster_names is not None:
                resource.clusters.set(
                    StorageCluster.objects.filter(name__in=cluster_names)
                )
                resource.save()

            self.set_custom_fields_values(resource, custom_field_data)
            self.set_tags(resource, tags)


register_initializer("storage_resources", StorageResourceInitializer)
