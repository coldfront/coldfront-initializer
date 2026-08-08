# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.ras.models import Project, ProjectUser
from coldfront.tenancy.models import Tenant
from coldfront.users.models import Group, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class ProjectInitializer(BaseInitializer):
    MODEL = Project
    REQUIRED_ASSOCS = {
        "owner": (User, "username"),
    }
    OPTIONAL_ASSOCS = {
        "tenant": (Tenant, "name"),
        "group": (Group, "name"),
    }

    def _pre_process(self, params):
        # Pop users before split_params so it doesn't end up in defaults
        self._usernames = params.pop("users", [])

    def _post_process(self, obj, created, params):
        for username in self._usernames:
            try:
                user = User.objects.get(username=username)
                _, created_pu = ProjectUser.objects.get_or_create(
                    user=user, project=obj
                )
                if created_pu:
                    logger.debug("Created project user: %s", username)
            except User.DoesNotExist:
                logger.warning(
                    "User '%s' not found, skipping for project %s",
                    username,
                    obj.name,
                )


register_initializer("projects", ProjectInitializer)
