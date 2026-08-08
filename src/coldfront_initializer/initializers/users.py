# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.users.models import ObjectPermission, Role, Token, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class UserInitializer(BaseInitializer):
    MODEL = User
    RECORDS_ARE_DICT = True
    PRIMARY_KEY = "username"
    MATCH_PARAMS = ["username"]

    def get_context(self):
        return {"users": User.objects.all()}

    def _pre_process(self, params):
        # Pop M2M and special fields before split_params
        self._api_token = params.pop("api_token", None)
        self._password = params.pop("password", None)
        self._password_hash = params.pop("password_hash", None)
        self._roles = params.pop("roles", [])
        self._permissions = params.pop("object_permissions", [])

    def _post_process(self, obj, created, params):
        if created:
            if self._password_hash:
                obj.password = self._password_hash
            elif self._password:
                obj.set_password(self._password)
            else:
                obj.set_unusable_password()
            obj.save()

            if self._api_token:
                token_key = (
                    Token.generate_key()
                    if self._api_token == "generate"
                    else self._api_token
                )
                Token.objects.get_or_create(user=obj, key=token_key)
                logger.debug("Created API token for user %s", obj.username)

        for role_name in self._roles:
            try:
                role = Role.objects.get(name=role_name)
                obj.roles.add(role)
                logger.debug("Assigned role %s to user %s", role_name, obj.username)
            except Role.DoesNotExist:
                logger.warning(
                    "Role '%s' not found, skipping for user %s",
                    role_name,
                    obj.username,
                )

        for perm_name in self._permissions:
            try:
                perm = ObjectPermission.objects.get(name=perm_name)
                obj.object_permissions.add(perm)
                logger.debug(
                    "Assigned object permission %s to user %s",
                    perm_name,
                    obj.username,
                )
            except ObjectPermission.DoesNotExist:
                logger.warning(
                    "ObjectPermission '%s' not found, skipping for user %s",
                    perm_name,
                    obj.username,
                )


register_initializer("users", UserInitializer)
