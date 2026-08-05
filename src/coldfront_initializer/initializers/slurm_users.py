# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmQOS, SlurmUser

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

MATCH_PARAMS = ["user", "cluster"]

REQUIRED_FK = {
    "user": (settings.AUTH_USER_MODEL, "username"),
    "cluster": (SlurmCluster, "name"),
}

OPTIONAL_FK = {
    "default_account": (SlurmAccount, "name"),
    "default_qos": (SlurmQOS, "name"),
}

ADMIN_LEVEL_MAP = {
    "None": 0,
    "Operator": 1,
    "Admin": 2,
}


class SlurmUserInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            # Resolve FK references
            for assoc, details in REQUIRED_FK.items():
                model, field = details
                query = {field: params.pop(assoc)}
                if isinstance(model, str):
                    from django.apps import apps

                    model_cls = apps.get_model(model)
                else:
                    model_cls = model
                params[assoc] = model_cls.objects.get(**query)

            # Resolve optional FK references
            for assoc, details in OPTIONAL_FK.items():
                if assoc in params:
                    val = params[assoc]
                    if val is None or val == "null":
                        params[assoc] = None
                        continue
                    model, field = details
                    query = {field: val}
                    try:
                        params[assoc] = model.objects.get(**query)
                    except model.DoesNotExist:
                        print(
                            f"⚠️  {model.__name__} with {field}='{val}' not found, "
                            f"setting {assoc}=None"
                        )
                        params[assoc] = None

            # Map admin_level string values to integer choices
            if "admin_level" in params:
                val = params["admin_level"]
                if val is None or val == "null":
                    params["admin_level"] = None
                else:
                    params["admin_level"] = ADMIN_LEVEL_MAP.get(val, val)

            matching_params, defaults = self.split_params(params, MATCH_PARAMS)

            # Use update_or_create because signal handlers (on_slurm_association_saved)
            # may have already created bare SlurmUser records (with default values).
            # get_or_create would return the existing record without applying our defaults.
            user_obj, created = SlurmUser.objects.update_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print("🖥️  Created SlurmUser", user_obj.user.username)


register_initializer("slurm_users", SlurmUserInitializer)
