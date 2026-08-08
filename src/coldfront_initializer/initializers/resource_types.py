# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.core.choices import ColorChoices
from coldfront.ras.models import ResourceType

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class ResourceTypeInitializer(BaseInitializer):
    MODEL = ResourceType

    def _pre_process(self, params):
        if "color" in params:
            color = params.pop("color")
            for color_tpl in ColorChoices:
                if color in color_tpl:
                    params["color"] = color_tpl[0]


register_initializer("resource_types", ResourceTypeInitializer)
