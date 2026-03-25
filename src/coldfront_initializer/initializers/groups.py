# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.users.models import Group, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class GroupInitializer(BaseInitializer):
    data_file_name = "groups.yml"

    def load_data(self):
        groups = self.load_yaml()
        if groups is None:
            return

        for groupname, group_details in groups.items():
            group, created = Group.objects.get_or_create(name=groupname)
            if created:
                print("👥 Created group", groupname)
            for username in group_details.get("users", []):
                user = User.objects.get(username=username)
                if user:
                    group.users.add(user)
                    print(" 👤 Assigned user %s to group %s" % (username, group.name))
            group.save()


register_initializer("groups", GroupInitializer)
