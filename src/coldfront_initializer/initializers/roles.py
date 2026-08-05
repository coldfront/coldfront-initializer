# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.users.models import ObjectPermission, Role

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class RoleInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for role_name, role_details in records.items():
            description = role_details.pop("description", "")
            weight = role_details.pop("weight", 100)
            permission_names = role_details.pop("object_permissions", [])

            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    "description": description,
                    "weight": weight,
                },
            )

            if created:
                print("🎭 Created Role", role_name)

            if permission_names:
                for perm_name in permission_names:
                    try:
                        perm = ObjectPermission.objects.get(name=perm_name)
                        role.object_permissions.add(perm)
                        print(
                            f" 🎭 Assigned object permission {perm_name} to role {role_name}"
                        )
                    except ObjectPermission.DoesNotExist:
                        print(
                            f" ⚠️ ObjectPermission '{perm_name}' not found, skipping"
                        )

            role.save()


register_initializer("roles", RoleInitializer)
