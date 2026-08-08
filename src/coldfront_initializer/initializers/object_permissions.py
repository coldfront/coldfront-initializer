# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.core.models import ObjectType
from coldfront.users.models import ObjectPermission

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class ObjectPermissionInitializer(BaseInitializer):
    MODEL = ObjectPermission
    RECORDS_ARE_DICT = True

    def _pre_process(self, params):
        # Pop M2M and special fields before split_params so they
        # don't end up in defaults and cause DirectAssignment errors
        self._object_types = params.pop("object_types", None)
        self._constraints = params.pop("constraints", None)

    def _post_process(self, obj, created, params):
        object_types = self._object_types
        constraints = self._constraints

        if constraints:
            obj.constraints = constraints

        if object_types:
            if object_types == "all":
                obj.object_types.set(ObjectType.objects.all())
            else:
                for app_label, models in object_types.items():
                    if models == "all":
                        app_models = ObjectType.objects.filter(app_label=app_label)
                        for app_model in app_models:
                            obj.object_types.add(app_model.id)
                    else:
                        for model in models:
                            obj.object_types.add(
                                ObjectType.objects.get(app_label=app_label, model=model)
                            )

        if constraints or object_types:
            obj.save()


register_initializer("object_permissions", ObjectPermissionInitializer)
