# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import (
    Allocation,
    AllocationUser,
    Project,
    ProjectUser,
    Resource,
)
from coldfront.tenancy.models import Tenant
from coldfront.users.models import User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

MATCH_PARAMS = ["owner", "project", "resource"]
REQUIRED_ASSOCS = {
    "owner": (User, "username"),
    "project": (Project, "name"),
    "resource": (Resource, "name"),
}
OPTIONAL_ASSOCS = {
    "tenant": (Tenant, "name"),
}


class AllocationInitializer(BaseInitializer):
    data_file_name = "allocations.yml"

    def load_data(self):
        allocations = self.load_yaml()
        if allocations is None:
            return

        for params in allocations:
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

            matching_params, defaults = self.split_params(params, MATCH_PARAMS)
            allocation, created = Allocation.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created allocation", allocation.slug)

            for u in users:
                user = User.objects.get(username=u)
                if not ProjectUser.objects.filter(
                    user=user, project=allocation.project
                ).exists():
                    raise Exception(
                        f"⚠️ User {u} has not been added to the project {allocation.project.name}"
                    )

                if user:
                    _, created = AllocationUser.objects.get_or_create(
                        user=user, allocation=allocation
                    )
                    if created:
                        print("👤  Created allocation user: ", u)

            self.set_custom_fields_values(allocation, custom_field_data)
            self.set_tags(allocation, tags)


register_initializer("allocations", AllocationInitializer)
