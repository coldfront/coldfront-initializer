# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.core.models import CustomFieldChoiceSet

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class CustomFieldChoiceSetInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            matching_params, defaults = self.split_params(params)
            choiceset, created = CustomFieldChoiceSet.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print(" Created choiceset", choiceset.name)


register_initializer("custom_field_choicesets", CustomFieldChoiceSetInitializer)
