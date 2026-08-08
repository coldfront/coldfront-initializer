# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.ras.models import Allocation, Project
from coldfront.tenancy.models import Tenant
from coldfront.users.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class AllocationInitializer(BaseInitializer):
    MODEL = Allocation
    REQUIRED_ASSOCS = {
        "owner": (User, "username"),
        "project": (Project, "name"),
    }
    OPTIONAL_ASSOCS = {
        "tenant": (Tenant, "name"),
    }
    MATCH_PARAMS = [
        "slug",
        "owner",
        "project",
        "resource_object_type",
        "resource_object_id",
    ]

    def parse_resource_object(self, value):
        if not value:
            raise ValueError("resource_object is required")

        ct_part, _, identifier_part = value.partition(":")
        if not identifier_part:
            raise ValueError(
                "resource_object must be in the format"
                ' "<app_label>.<model>:<identifier>"'
            )
        app_label, model = ct_part.split(".")

        try:
            ct = ContentType.objects.get_by_natural_key(
                app_label=app_label, model=model
            )
        except ObjectDoesNotExist:
            raise ValueError(
                'Invalid content type: "{app_label}.{model}"'
                " for resource_object".format(app_label=app_label, model=model)
            )

        model_class = ct.model_class()
        if model_class is None:
            raise ValueError("resource_object model class not found for content type")

        if "=" in identifier_part:
            field_name, _, field_value = identifier_part.partition("=")
            field_name = field_name.strip()
            field_value = field_value.strip()
        else:
            field_name = "name"
            field_value = identifier_part.strip()

        try:
            filter_kwargs = {field_name: field_value}
            obj = model_class.objects.get(**filter_kwargs)
        except ObjectDoesNotExist:
            raise ValueError("resource_object not found: {value}".format(value=value))
        except MultipleObjectsReturned:
            raise ValueError(
                '"resource_object {value}" matched multiple objects'.format(value=value)
            )

        return obj

    def _pre_process(self, params):
        try:
            resource_obj = self.parse_resource_object(
                params.pop("resource_object", None)
            )
            params["resource_object_type"] = ContentType.objects.get_for_model(
                resource_obj
            )
            params["resource_object_id"] = resource_obj.pk
        except ValueError as e:
            logger.warning("Unable to create Allocation: %s", e)
            params["_skip"] = True

    def load_data(self, records):
        if records is None:
            return

        for params in records:
            self._pre_process(params)
            if params.pop("_skip", False):
                continue

            custom_field_data = self._pop_custom_fields(params)
            tags = self._pop_tags(params)
            create_date = self._pop_created(params)

            self.resolve_required(params)
            self.resolve_optional(params)

            matching_params, defaults = self.split_params(params, self.MATCH_PARAMS)
            obj, created = self._model.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                if create_date:
                    self.set_create_date(obj, create_date)
                logger.debug("Created allocation %s", obj.slug)

            self.set_custom_fields_values(obj, custom_field_data)
            self.set_tags(obj, tags)


register_initializer("allocations", AllocationInitializer)
