# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.users.models import Token, User
from django.utils.crypto import get_random_string

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
            password = user_details.pop("password", get_random_string(length=25))
            user, created = User.objects.get_or_create(
                username=username, defaults=user_details
            )
            if created:
                user.set_password(password)
                user.save()
                if api_token:
                    api_token = (
                        Token.generate_key() if api_token == "generate" else api_token
                    )
                    Token.objects.get_or_create(user=user, key=api_token)
                print("👤 Created user", username)


register_initializer("users", UserInitializer)
