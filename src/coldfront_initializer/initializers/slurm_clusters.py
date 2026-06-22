# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmCluster, SlurmQOS
from coldfront.tenancy.models import Tenant

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

OPTIONAL_FK = {
    "tenant": (Tenant, "name"),
    "default_qos": (SlurmQOS, "name"),
}


class SlurmClusterInitializer(BaseInitializer):
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

            # Resolve M2M references
            qos_list = params.pop("qos_list", None)

            matching_params, defaults = self.split_params(params)
            cluster, created = SlurmCluster.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created SlurmCluster", cluster.name)

            # Set M2M values after creation
            if qos_list is not None:
                cluster.qos_list.set(
                    SlurmQOS.objects.filter(name__in=qos_list)
                )
                cluster.save()

            self.set_custom_fields_values(cluster, custom_field_data)
            self.set_tags(cluster, tags)


register_initializer("slurm_clusters", SlurmClusterInitializer)
