# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.core.models import CommentEntry
from coldfront.users.models import User
from django.contrib.contenttypes.models import ContentType

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    LoadResult,
    register_initializer,
)

logger = logging.getLogger(__name__)


class CommentEntryInitializer(BaseInitializer):
    MODEL = CommentEntry
    OPTIONAL_ASSOCS = {
        "created_by": (User, "username"),
    }

    def _parse_assigned_object(self, value):
        """Parse an assigned_object reference like ``ras.allocation:slug=a1000001``
        into a ContentType + object pk for the GenericForeignKey."""
        if not value:
            raise ValueError("assigned_object is required")

        ct_part, _, identifier_part = value.partition(":")
        if not identifier_part:
            raise ValueError(
                "assigned_object must be in the format"
                ' "<app_label>.<model>:<identifier>"'
            )
        app_label, model = ct_part.split(".")

        ct = ContentType.objects.get_by_natural_key(app_label=app_label, model=model)
        model_class = ct.model_class()
        if model_class is None:
            raise ValueError("assigned_object model class not found for content type")

        if "=" in identifier_part:
            field_name, _, field_value = identifier_part.partition("=")
            field_name = field_name.strip()
            field_value = field_value.strip()
        else:
            field_name = "name"
            field_value = identifier_part.strip()

        obj = model_class.objects.get(**{field_name: field_value})
        return ct, obj.pk

    def _pre_process(self, params):
        try:
            ct, obj_id = self._parse_assigned_object(
                params.pop("assigned_object", None)
            )
        except Exception as e:
            logger.warning("Unable to create CommentEntry: %s", e)
            params["_skip"] = True
            params["_skip_reason"] = f"Unable to create CommentEntry: {e}"
            return
        params["assigned_object_type"] = ct
        params["assigned_object_id"] = obj_id

    def load_data(self, records):
        """Comments are historical records — always create a new row rather
        than dedupe with get_or_create, so multiple comments per object are
        supported."""
        if records is None:
            return None

        result = LoadResult(found=len(records))
        self._result = result

        for params in records:
            try:
                self._pre_process(params)
                if params.pop("_skip", False):
                    self._skip(params.pop("_skip_reason", None))
                    continue

                custom_field_data = self._pop_custom_fields(params)
                tags = self._pop_tags(params)
                create_date = self._pop_created(params)

                if not self._has_slug:
                    params.pop("slug", None)

                self.resolve_optional(params)

                obj = self._model.objects.create(**params)
                logger.debug(
                    "Created %s: %s",
                    self._model.__name__,
                    self._display_name(obj),
                )

                if create_date and self._supports_created():
                    self.set_create_date(obj, create_date)

                self.set_custom_fields_values(obj, custom_field_data)
                self.set_tags(obj, tags)

                self._ok(obj, True)
            except Exception as e:
                self._fail(str(e))

        return result


register_initializer("comment_entries", CommentEntryInitializer)
