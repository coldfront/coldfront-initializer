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
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)
            users = params.pop("users", [])
            create_date = params.pop("created", None)

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
                self.set_create_date(allocation, create_date)
                print("🖥️  Created allocation", allocation.slug)

            for u in users:
                user = User.objects.get(username=u)
                if not ProjectUser.objects.filter(
                    user=user, project=allocation.project
                ).exists():
                    print(
                        f"⚠️ Unable to add user '{u}' to allocation because they have not been added to project {allocation.project.name}"
                    )
                    continue

                if user:
                    _, created = AllocationUser.objects.get_or_create(
                        user=user, allocation=allocation
                    )
                    if created:
                        print("👤  Created allocation user: ", u)

            self.set_custom_fields_values(allocation, custom_field_data)
            self.set_tags(allocation, tags)


register_initializer("allocations", AllocationInitializer)
