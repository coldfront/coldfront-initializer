# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Project, ProjectUser
from coldfront.tenancy.models import Tenant
from coldfront.users.models import User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

REQUIRED_ASSOCS = {
    "owner": (User, "username"),
}
OPTIONAL_ASSOCS = {
    "tenant": (Tenant, "name"),
}


class ProjectInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)
            users = params.pop("users", [])

            for assoc, details in REQUIRED_ASSOCS.items():
                model, field = details
                query = {field: params.pop(assoc)}

                params[assoc] = model.objects.get(**query)

            for assoc, details in OPTIONAL_ASSOCS.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            matching_params, defaults = self.split_params(params)
            project, created = Project.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created project", project.name)

            for u in users:
                user = User.objects.get(username=u)
                if user:
                    _, created = ProjectUser.objects.get_or_create(
                        user=user, project=project
                    )
                    if created:
                        print("👤  Created project user: ", u)

            self.set_custom_fields_values(project, custom_field_data)
            self.set_tags(project, tags)


register_initializer("projects", ProjectInitializer)
