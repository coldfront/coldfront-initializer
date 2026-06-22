# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmPartition, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


REQUIRED_FK = {
    "cluster": (SlurmCluster, "name"),
}

OPTIONAL_M2M = {
    "qos_list": (SlurmQOS, "name"),
    "allow_groups": ("users.Group", "name"),
    "allow_accounts": (SlurmAccount, "name"),
}


class SlurmPartitionInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            # Resolve FK references
            for assoc, details in REQUIRED_FK.items():
                model, field = details
                query = {field: params.pop(assoc)}
                params[assoc] = model.objects.get(**query)

            # Collect M2M references before they are popped by split_params
            m2m_values = {}
            for assoc, details in OPTIONAL_M2M.items():
                if assoc in params:
                    m2m_values[assoc] = params.pop(assoc)

            matching_params, defaults = self.split_params(params)
            partition, created = SlurmPartition.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created SlurmPartition", partition.name)

            # Set M2M values after creation
            for assoc, details in OPTIONAL_M2M.items():
                if assoc in m2m_values:
                    model, field = details
                    if isinstance(model, str):
                        # Lazy import for string-based model references
                        from django.apps import apps

                        model_cls = apps.get_model(model)
                    else:
                        model_cls = model
                    getattr(partition, assoc).set(
                        model_cls.objects.filter(
                            **{field + "__in": m2m_values[assoc]}
                        )
                    )

            partition.save()

            self.set_custom_fields_values(partition, custom_field_data)
            self.set_tags(partition, tags)


register_initializer("slurm_partitions", SlurmPartitionInitializer)
