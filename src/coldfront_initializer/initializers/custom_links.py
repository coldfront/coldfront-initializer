# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.core.models import CustomLink, ObjectType

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class CustomLinkInitializer(BaseInitializer):
    MODEL = CustomLink
    MATCH_PARAMS = ["name"]

    def _pre_process(self, params):
        # Pop M2M field before split_params so it doesn't end up in defaults
        self._object_types = params.pop("object_types", None)

    def _post_process(self, obj, created, params):
        object_types = self._object_types
        if not created or not object_types:
            return
        for ot in object_types:
            ct = ObjectType.objects.get(app_label=ot["app"], model=ot["model"])
            obj.object_types.add(ct)
            logger.debug(
                "Applied CustomLink %s to %s.%s", obj.name, ot["app"], ot["model"]
            )


register_initializer("custom_links", CustomLinkInitializer)
