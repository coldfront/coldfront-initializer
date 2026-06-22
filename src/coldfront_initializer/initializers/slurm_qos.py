# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class SlurmQOSInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            matching_params, defaults = self.split_params(params)
            qos, created = SlurmQOS.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created SlurmQOS", qos.name)

            self.set_custom_fields_values(qos, custom_field_data)
            self.set_tags(qos, tags)


register_initializer("slurm_qos", SlurmQOSInitializer)
