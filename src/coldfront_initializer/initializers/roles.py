# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.users.models import ObjectPermission, Role

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class RoleInitializer(BaseInitializer):
    MODEL = Role
    RECORDS_ARE_DICT = True

    def _pre_process(self, params):
        # Pop M2M field before split_params so it doesn't end up in defaults
        self._permission_names = params.pop("object_permissions", [])

    def _post_process(self, obj, created, params):
        for perm_name in self._permission_names:
            try:
                perm = ObjectPermission.objects.get(name=perm_name)
                obj.object_permissions.add(perm)
                logger.debug(
                    "Assigned object permission %s to role %s", perm_name, obj.name
                )
            except ObjectPermission.DoesNotExist:
                logger.warning("ObjectPermission '%s' not found, skipping", perm_name)


register_initializer("roles", RoleInitializer)
