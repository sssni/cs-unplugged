"""Custom loader for loading age group."""

import os.path

from django.db import transaction

from utils.BaseLoader import BaseLoader
from utils.errors.MissingRequiredFieldError import MissingRequiredFieldError
from utils.errors.CouldNotFindMarkdownFileError import CouldNotFindMarkdownFileError

from topics.models import AgeGroup


class AgeGroupsLoader(BaseLoader):
    """Loader for age group content."""

    def __init__(self, **kwargs):
        """Create the loader for loading age groups.

        Args:
            structure_file_path: File path to YAML file (str).
        """
        # inner_path, structure_file = os.path.split(structure_file_path)
        super().__init__(**kwargs)
        # self.structure_file_path = structure_file_path

    @transaction.atomic
    def load(self):
        """Load the content for age groups.

        Raise:
            MissingRequiredFieldError: when no object can be found with the
                matching attribute.
        """
        age_groups_structure = self.load_yaml_file(self.structure_file_path)

        for (age_group_slug, age_group_data) in age_groups_structure.items():

            if age_group_data is None:
                raise MissingRequiredFieldError(
                    self.structure_file_path,
                    ["min_age", "max_age"],
                    "Age Range"
                )

            group_min_age = age_group_data.get("min_age", None)
            if group_min_age is None:
                raise MissingRequiredFieldError(
                    self.structure_file_path,
                    ["min_age"],
                    "Age Range"
                )

            group_max_age = age_group_data.get("max_age", None)
            if group_max_age is None:
                raise MissingRequiredFieldError(
                    self.structure_file_path,
                    ["max_age"],
                    "Age Range"
                )

            group_description = age_group_data.get("description", None)

            # Create area objects and save to database
            age_group = AgeGroup(
                slug=age_group_slug,
                ages=(int(group_min_age), int(group_max_age)),
                description=group_description,
            )
            age_group.save()

            self.log("Added age group: {}".format(age_group.__str__()))

        self.log("All age groups loaded!\n")
