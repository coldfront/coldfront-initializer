# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

REQUIRED_FK = {
    "cluster": (SlurmCluster, "name"),
}

OPTIONAL_M2M = {
    "qos_list": (SlurmQOS, "name"),
}


class SlurmAccountInitializer(BaseInitializer):
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

            # Collect M2M references before they are popped
            m2m_values = {}
            for assoc, details in OPTIONAL_M2M.items():
                if assoc in params:
                    m2m_values[assoc] = params.pop(assoc)

            matching_params, defaults = self.split_params(
                params, unique_params=["name", "cluster"]
            )
            account, created = SlurmAccount.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created SlurmAccount", account.name)

            # Set M2M values after creation
            for assoc, details in OPTIONAL_M2M.items():
                if assoc in m2m_values:
                    model, field = details
                    getattr(account, assoc).set(
                        model.objects.filter(**{field + "__in": m2m_values[assoc]})
                    )

            account.save()

            self.set_custom_fields_values(account, custom_field_data)
            self.set_tags(account, tags)


register_initializer("slurm_accounts", SlurmAccountInitializer)
