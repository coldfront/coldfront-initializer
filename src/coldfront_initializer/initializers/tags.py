# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.core.choices import ColorChoices
from coldfront.core.models import ObjectType, Tag

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class TagInitializer(BaseInitializer):
    MODEL = Tag

    def _pre_process(self, params):
        if "color" in params:
            color = params.pop("color")
            for color_tpl in ColorChoices:
                if color in color_tpl:
                    params["color"] = color_tpl[0]

        # Pop M2M field before split_params
        self._object_types = params.pop("object_types", None)

    def _post_process(self, obj, created, params):
        if not created:
            return
        object_types = self._object_types
        if not object_types:
            return
        for ot in object_types:
            ct = ObjectType.objects.get(
                app_label=ot["app"],
                model=ot["model"],
            )
            obj.object_types.add(ct)
            logger.debug("Restricted Tag %s to %s.%s", obj.name, ot["app"], ot["model"])


register_initializer("tags", TagInitializer)
