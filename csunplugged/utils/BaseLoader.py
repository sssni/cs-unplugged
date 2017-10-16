"""Base loader used to create custom loaders for content."""

import yaml
import mdx_math
import abc
import sys
import re
import os.path
from os import listdir
from verto import Verto
from verto.errors.StyleError import StyleError

from .check_required_files import check_converter_required_files
from .check_glossary_links import check_converter_glossary_links
from utils.errors.CouldNotFindMarkdownFileError import CouldNotFindMarkdownFileError
from utils.errors.MarkdownStyleError import MarkdownStyleError
from utils.errors.EmptyMarkdownFileError import EmptyMarkdownFileError
from utils.errors.EmptyConfigFileError import EmptyConfigFileError
from utils.errors.InvalidConfigFileError import InvalidConfigFileError
from utils.errors.NoHeadingFoundInMarkdownFileError import NoHeadingFoundInMarkdownFileError
from utils.errors.CouldNotFindConfigFileError import CouldNotFindConfigFileError


class BaseLoader():
    """Base loader class for individual loaders."""

    def __init__(self, BASE_PATH="", STRUCTURE_DIR='en', INNER_PATH="", STRUCTURE_FILE=""):
        """Create a BaseLoader object.

        Args:
            BASE_PATH: string of base content path, which stores has one directory
                       per locale, plus a special structure directory (str).
            STRUCTURE_DIR: directory after BASE_PATH in which
                           language-independent structure files are stored (str).
            INNER_PATH: Path from locale/structure direcory to required directory (str).
            YAML_FILENAME: Path to YAML file
        """
        self.BASE_PATH = BASE_PATH
        self.STRUCTURE_DIR = STRUCTURE_DIR
        self.INNER_PATH = INNER_PATH
        self.STRUCTURE_FILE = STRUCTURE_FILE
        self.setup_md_to_html_converter()

    def get_locale_path(self, locale, filename):
        return self.get_full_path(locale, filename)

    def get_full_path(self, locale_or_structure_dir, filename):
        if filename:
            return os.path.join(self.BASE_PATH, locale_or_structure_dir, self.INNER_PATH, filename)
        else:
            return os.path.join(self.BASE_PATH, locale_or_structure_dir, self.INNER_PATH)

    @property
    def structure_file_path(self):
        return self.get_full_path(self.STRUCTURE_DIR, self.STRUCTURE_FILE)

    def setup_md_to_html_converter(self):
        """Create Markdown converter.

        The converter is created with custom processors, html templates,
        and extensions.
        """
        templates = self.load_template_files()
        extensions = [
            "markdown.extensions.fenced_code",
            "markdown.extensions.codehilite",
            "markdown.extensions.sane_lists",
            "markdown.extensions.tables",
            mdx_math.MathExtension()
        ]
        self.converter = Verto(html_templates=templates, extensions=extensions)

    def convert_md_file(self, md_file_path, config_file_path, heading_required=True, remove_title=True):
        """Return the Verto object for a given Markdown file.

        Args:
            md_file_path: Location of Markdown file to convert (str).
            config_file_path: Path to related the config file (str).
            heading_required: Boolean if the file requires a heading (bool).
            remove_title: Boolean if the file's first heading should be removed (bool).

        Returns:
            VertoResult object

        Raises:
            CouldNotFindMarkdownFileError: when a given Markdown file cannot be found.
            NoHeadingFoundInMarkdownFileError: when no heading can be found in a given
                Markdown file.
            EmptyMarkdownFileError: when no content can be found in a given Markdown
                file.
            MarkdownStyleError: when a verto StyleError is thrown.
        """
        try:
            # check file exists
            content = open(md_file_path, encoding="UTF-8").read()
        except:
            raise CouldNotFindMarkdownFileError(md_file_path, config_file_path)

        custom_processors = self.converter.processor_defaults()
        if remove_title:
            custom_processors.add("remove-title")
        self.converter.update_processors(custom_processors)

        result = None
        try:
            result = self.converter.convert(content)
        except StyleError as e:
            raise MarkdownStyleError(md_file_path, e) from e

        if heading_required:
            if result.title is None:
                raise NoHeadingFoundInMarkdownFileError(md_file_path)

        if len(result.html_string) == 0:
            raise EmptyMarkdownFileError(md_file_path)
        check_converter_required_files(result.required_files, md_file_path)
        check_converter_glossary_links(result.required_glossary_terms, md_file_path)
        return result

    def log(self, message, indent_amount=0):
        """Output the log message to the load log.

        Args:
            message: Text to display (str).
            indent_amount: Amount of indentation required (int).
        """
        indent = "  " * indent_amount
        text = "{indent}{text}\n".format(indent=indent, text=message)
        sys.stdout.write(text)

    def load_yaml_file(self, yaml_file_path):
        """Load and read given YAML file.

        Args:
            file_path: location of yaml file to read (str).

        Returns:
            Either list or string, depending on structure of given yaml file

        Raises:
            CouldNotFindConfigFileError: when a given config file cannot be found.
            InvalidConfigFileError: when a given config file is incorrectly formatted.
            EmptyConfigFileError: when a give config file is empty.
        """
        try:
            yaml_file = open(yaml_file_path, encoding="UTF-8").read()
        except:
            raise CouldNotFindConfigFileError(yaml_file_path)

        try:
            yaml_contents = yaml.load(yaml_file)
        except:
            raise InvalidConfigFileError(yaml_file_path)

        if yaml_contents is None:
            raise EmptyConfigFileError(yaml_file_path)

        if isinstance(yaml_contents, dict) is False:
            raise InvalidConfigFileError(yaml_file_path)

        return yaml_contents

    def load_template_files(self):
        """Load custom HTML templates for converter.

        Returns:
            templates: dictionary of html templates
        """
        templates = dict()
        template_path = os.path.join(
            os.path.dirname(__file__),
            "custom_converter_templates/"
        )
        for file in listdir(template_path):
            template_file = re.search(r"(.*?).html$", file)
            if template_file:
                template_name = template_file.groups()[0]
                templates[template_name] = open(template_path + file).read()
        return templates

    @abc.abstractmethod
    def load(self):
        """Abstract method to be implemented by subclasses.

        Raise:
            NotImplementedError: when a user attempts to run the load() method of the
                BaseLoader class.
        """
        raise NotImplementedError("Subclass does not implement this method")
