# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.core.choices import ColorChoices
from coldfront.ras.models import ResourceType
from coldfront.utils.jsonschema import validate_schema

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class ResourceTypeInitializer(BaseInitializer):
    data_file_name = "resource_types.yml"

    def load_data(self):
        resource_types = self.load_yaml()
        if resource_types is None:
            return

        for params in resource_types:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            if "color" in params:
                color = params.pop("color")

                for color_tpl in ColorChoices:
                    if color in color_tpl:
                        params["color"] = color_tpl[0]

            for schema in ["schema", "allocation_schema"]:
                validate_schema(params[schema])

            matching_params, defaults = self.split_params(params)
            resource_type, created = ResourceType.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created ResourceType", resource_type.name)

            self.set_custom_fields_values(resource_type, custom_field_data)
            self.set_tags(resource_type, tags)


register_initializer("resource_types", ResourceTypeInitializer)
