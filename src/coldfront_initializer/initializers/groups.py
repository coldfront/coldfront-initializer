# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.users.models import Group, ObjectPermission, Role, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class GroupInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for groupname, group_details in records.items():
            roles = group_details.pop("roles", [])
            permissions = group_details.pop("object_permissions", [])
            group, created = Group.objects.get_or_create(name=groupname)
            if created:
                print("👥 Created group", groupname)

            for username in group_details.get("users", []):
                user = User.objects.get(username=username)
                if user:
                    group.users.add(user)
                    print(f" 👤 Assigned user {username} to group {group.name}")

            if roles:
                for role_name in roles:
                    try:
                        role = Role.objects.get(name=role_name)
                        group.roles.add(role)
                        print(f" 👥 Assigned role {role_name} to group {groupname}")
                    except Role.DoesNotExist:
                        print(
                            f" ⚠️ Role '{role_name}' not found, skipping for group {groupname}"
                        )

            if permissions:
                for perm_name in permissions:
                    try:
                        perm = ObjectPermission.objects.get(name=perm_name)
                        group.object_permissions.add(perm)
                        print(
                            f" 👥 Assigned object permission {perm_name} to group {groupname}"
                        )
                    except ObjectPermission.DoesNotExist:
                        print(
                            f" ⚠️ ObjectPermission '{perm_name}' not found, skipping for group {groupname}"
                        )

            group.save()


register_initializer("groups", GroupInitializer)
