# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.users.models import Group, ObjectPermission, Role, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class GroupInitializer(BaseInitializer):
    MODEL = Group
    RECORDS_ARE_DICT = True

    def _pre_process(self, params):
        # Pop M2M fields before split_params
        self._usernames = params.pop("users", [])
        self._role_names = params.pop("roles", [])
        self._perm_names = params.pop("object_permissions", [])

    def _post_process(self, obj, created, params):
        for username in self._usernames:
            try:
                user = User.objects.get(username=username)
                obj.users.add(user)
                logger.debug("Assigned user %s to group %s", username, obj.name)
            except User.DoesNotExist:
                logger.warning(
                    "User '%s' not found, skipping for group %s",
                    username,
                    obj.name,
                )

        for role_name in self._role_names:
            try:
                role = Role.objects.get(name=role_name)
                obj.roles.add(role)
                logger.debug("Assigned role %s to group %s", role_name, obj.name)
            except Role.DoesNotExist:
                logger.warning(
                    "Role '%s' not found, skipping for group %s",
                    role_name,
                    obj.name,
                )

        for perm_name in self._perm_names:
            try:
                perm = ObjectPermission.objects.get(name=perm_name)
                obj.object_permissions.add(perm)
                logger.debug(
                    "Assigned object permission %s to group %s",
                    perm_name,
                    obj.name,
                )
            except ObjectPermission.DoesNotExist:
                logger.warning(
                    "ObjectPermission '%s' not found, skipping for group %s",
                    perm_name,
                    obj.name,
                )

        obj.save()


register_initializer("groups", GroupInitializer)
