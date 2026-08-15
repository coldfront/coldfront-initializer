# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.ras.models import Project
from coldfront.ris.models import Publication
from coldfront.users.models import User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class PublicationInitializer(BaseInitializer):
    MODEL = Publication
    OPTIONAL_ASSOCS = {
        "created_by": (User, "username"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "projects": (Project, "slug"),
    }
    # The DOI is the canonical identity of a publication.
    MATCH_PARAMS = ["doi"]


register_initializer("publications", PublicationInitializer)
