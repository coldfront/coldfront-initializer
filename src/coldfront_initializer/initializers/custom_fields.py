# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.core.models import CustomField, CustomFieldChoiceSet

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    LoadResult,
    register_initializer,
)

logger = logging.getLogger(__name__)


def get_class_for_class_path(class_path):
    import importlib

    from coldfront.core.models import ObjectType

    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    clazz = getattr(module, class_name)
    return ObjectType.objects.get_for_model(clazz)


# Fields in the YAML that are NOT direct model fields
NON_MODEL_FIELDS = (
    "on_objects",
    "choices",
    "related_object_type",
    "validation_regex",
    "validation_minimum",
    "validation_maximum",
    "ui_visibility",  # model has ui_visible, not ui_visibility
    "ui_editable",  # model has ui_editable — this one IS a field actually
)


class CustomFieldInitializer(BaseInitializer):
    MODEL = CustomField
    RECORDS_ARE_DICT = True

    def load_data(self, records):
        if records is None:
            return None

        items = self._normalize_records(records)
        result = LoadResult(found=len(items))
        self._result = result

        for params in items:
            try:
                cf_type = params.get("type")

                # --- Type-specific validations (skip if invalid) ---
                if params.get("validation_regex") and cf_type not in (
                    "text",
                    "longtext",
                    "url",
                ):
                    self._skip(
                        "Unable to create Custom Field "
                        f"'{params.get(self.PRIMARY_KEY)}': validation_regex is "
                        "supported only for text, longtext and url types"
                    )
                    continue

                if params.get("validation_minimum") and cf_type not in ("integer",):
                    self._skip(
                        "Unable to create Custom Field "
                        f"'{params.get(self.PRIMARY_KEY)}': validation_minimum is "
                        "supported only for integer type"
                    )
                    continue

                if params.get("validation_maximum") and cf_type not in ("integer",):
                    self._skip(
                        "Unable to create Custom Field "
                        f"'{params.get(self.PRIMARY_KEY)}': validation_maximum is "
                        "supported only for integer type"
                    )
                    continue

                if params.get("choices") and cf_type not in ("select", "multiselect"):
                    self._skip(
                        "Unable to create Custom Field "
                        f"'{params.get(self.PRIMARY_KEY)}': choices is supported "
                        "only for select and multiselect types"
                    )
                    continue

                if params.get("related_object_type") and cf_type not in (
                    "object",
                    "multiobject",
                ):
                    self._skip(
                        "Unable to create Custom Field "
                        f"'{params.get(self.PRIMARY_KEY)}': related_object_type is "
                        "supported only for object and multiobject types"
                    )
                    continue

                # --- Pop non-model fields before split_params ---
                on_objects = params.pop("on_objects", None)
                choices = params.pop("choices", None)
                related_object_type = params.pop("related_object_type", None)
                validation_regex = params.pop("validation_regex", None)
                validation_minimum = params.pop("validation_minimum", None)
                validation_maximum = params.pop("validation_maximum", None)
                ui_visibility = params.pop("ui_visibility", None)

                # CustomField has no custom_field_data or tags support
                create_date = self._pop_created(params)

                matching_params, defaults = self.split_params(
                    params, unique_params=["name"]
                )
                obj, created = self._model.objects.get_or_create(
                    **matching_params, defaults=defaults
                )

                if created:
                    logger.debug("Created custom field %s", obj.name)

                    # --- Apply field values ---
                    if params.get("default"):
                        obj.default = params["default"]
                    if params.get("description"):
                        obj.description = params["description"]
                    if params.get("label"):
                        obj.label = params["label"]
                    if params.get("required"):
                        obj.required = params["required"]
                    if params.get("type"):
                        obj.type = params["type"]
                    if params.get("filter_logic"):
                        obj.filter_logic = params["filter_logic"]
                    if params.get("weight", -1) >= 0:
                        obj.weight = params["weight"]
                    if params.get("group_name"):
                        obj.group_name = params["group_name"]
                    if params.get("ui_editable"):
                        obj.ui_editable = params["ui_editable"]
                    if ui_visibility:
                        obj.ui_visible = ui_visibility
                    if params.get("search_weight", -1) >= 0:
                        obj.search_weight = params["search_weight"]
                    if params.get("is_cloneable", None) is not None:
                        obj.is_cloneable = params["is_cloneable"]
                    if params.get("required_action", None) is not None:
                        obj.required_action = params["required_action"]

                    # on_objects
                    if on_objects:
                        for object_type in on_objects:
                            obj.object_types.add(get_class_for_class_path(object_type))

                    # related_object_type
                    if related_object_type:
                        obj.related_object_type = get_class_for_class_path(
                            related_object_type
                        )

                    # validation fields
                    if validation_regex:
                        obj.validation_regex = validation_regex
                    if validation_minimum:
                        obj.validation_minimum = validation_minimum
                    if validation_maximum:
                        obj.validation_maximum = validation_maximum

                    # choices
                    if choices:
                        choice_set, _ = CustomFieldChoiceSet.objects.get_or_create(
                            name=f"{obj.name}_choices",
                            choices=choices,
                        )
                        obj.choice_set = choice_set

                    obj.save()

                    if create_date:
                        self.set_create_date(obj, create_date)

                self._ok(obj, created)
            except Exception as e:
                self._fail(str(e))

        return result


register_initializer("custom_fields", CustomFieldInitializer)
