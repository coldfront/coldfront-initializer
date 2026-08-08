# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.core.models import CustomFieldChoiceSet

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class CustomFieldChoiceSetInitializer(BaseInitializer):
    MODEL = CustomFieldChoiceSet


register_initializer("custom_field_choicesets", CustomFieldChoiceSetInitializer)
