# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.users.models import ObjectPermission, Role, Token, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class UserInitializer(BaseInitializer):
    def get_context(self):
        return {"users": User.objects.all()}

    def load_data(self, records):
        if records is None:
            return

        for username, user_details in records.items():
            api_token = user_details.pop("api_token", None)
            password = user_details.pop("password", None)
            password_hash = user_details.pop("password_hash", None)
            roles = user_details.pop("roles", [])
            permissions = user_details.pop("object_permissions", [])
            user, created = User.objects.get_or_create(
                username=username, defaults=user_details
            )
            if created:
                if password_hash:
                    user.password = password_hash
                elif password:
                    user.set_password(password)
                else:
                    user.set_unusable_password()

                user.save()

                if api_token:
                    api_token = (
                        Token.generate_key() if api_token == "generate" else api_token
                    )
                    Token.objects.get_or_create(user=user, key=api_token)
                print("👤 Created user", username)

            if roles:
                for role_name in roles:
                    try:
                        role = Role.objects.get(name=role_name)
                        user.roles.add(role)
                        print(f" 👤 Assigned role {role_name} to user {username}")
                    except Role.DoesNotExist:
                        print(
                            f" ⚠️ Role '{role_name}' not found, skipping for user {username}"
                        )

            if permissions:
                for perm_name in permissions:
                    try:
                        perm = ObjectPermission.objects.get(name=perm_name)
                        user.object_permissions.add(perm)
                        print(
                            f" 👤 Assigned object permission {perm_name} to user {username}"
                        )
                    except ObjectPermission.DoesNotExist:
                        print(
                            f" ⚠️ ObjectPermission '{perm_name}' not found, skipping for user {username}"
                        )


register_initializer("users", UserInitializer)
