# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class StorageClusterInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            matching_params, defaults = self.split_params(params)
            cluster, created = StorageCluster.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created StorageCluster", cluster.name)

            self.set_custom_fields_values(cluster, custom_field_data)
            self.set_tags(cluster, tags)


register_initializer("storage_clusters", StorageClusterInitializer)
