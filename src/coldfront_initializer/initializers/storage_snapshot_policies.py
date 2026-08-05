# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster, StorageSnapshotPolicy

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

OPTIONAL_FK = {
    "cluster": (StorageCluster, "name"),
}


class StorageSnapshotPolicyInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            # Resolve FK references
            for assoc, details in OPTIONAL_FK.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            matching_params, defaults = self.split_params(params)
            policy, created = StorageSnapshotPolicy.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created StorageSnapshotPolicy", policy.name)

            self.set_custom_fields_values(policy, custom_field_data)
            self.set_tags(policy, tags)


register_initializer("storage_snapshot_policies", StorageSnapshotPolicyInitializer)
