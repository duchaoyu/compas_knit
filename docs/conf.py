# flake8: noqa
# -*- coding: utf-8 -*-
# The documentation, in the style of the COMPAS packages, with sphinx_compas2_theme.
#     sphinx-build -b html docs docs/_build/html

import os
import sys

from sphinx.writers import html, html5
import sphinx_compas2_theme

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

# -- General configuration ------------------------------------------------

project = "compas_knit"
copyright = "Chaoyu Du"
author = "Chaoyu Du"
organization = "duchaoyu"
package = "compas_knit"

master_doc = "index"
source_suffix = {".rst": "restructuredtext"}
templates_path = sphinx_compas2_theme.get_autosummary_templates_path()
exclude_patterns = sphinx_compas2_theme.default_exclude_patterns + ["book", "_build"]
add_module_names = True
language = "en"

release = "0.1.0"
version = ".".join(release.split(".")[0:2])

# -- Extension configuration ------------------------------------------------

extensions = sphinx_compas2_theme.default_extensions

# numpydoc options

numpydoc_show_class_members = False
numpydoc_class_members_toctree = False
numpydoc_attributes_as_param_list = True
numpydoc_show_inherited_class_members = False

# autodoc options

autodoc_type_aliases = {}
autodoc_typehints_description_target = "documented"
autodoc_mock_imports = sphinx_compas2_theme.default_mock_imports
autodoc_default_options = {
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_member_order = "groupwise"
autodoc_typehints = "description"
autodoc_class_signature = "separated"

autoclass_content = "class"


def setup(app):
    app.connect("autodoc-skip-member", sphinx_compas2_theme.skip)


# autosummary options

autosummary_generate = True
autosummary_mock_imports = sphinx_compas2_theme.default_mock_imports

# intersphinx options

intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
    "compas": ("https://compas.dev/compas/latest/", None),
}

# linkcode: the source of each function on GitHub

linkcode_resolve = sphinx_compas2_theme.get_linkcode_resolve(organization, package)

# extlinks

extlinks = {}

# from pytorch

sphinx_compas2_theme.replace(html.HTMLTranslator)
sphinx_compas2_theme.replace(html5.HTML5Translator)

# -- Options for HTML output ----------------------------------------------

html_theme = "sidebaronly"
html_title = project
html_sidebars = {"index": []}

html_theme_options = {
    "external_links": [
        {"name": "COMPAS Framework", "url": "https://compas.dev"},
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": f"https://github.com/{organization}/{package}",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
    ],
    "logo": {
        "text": project,
    },
    "navigation_depth": 2,
    # no version switcher: it needs the versions.json of published versions
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
}

html_context = {
    "github_url": "https://github.com",
    "github_user": organization,
    "github_repo": package,
    "github_version": "main",
    "doc_path": "docs",
}

html_static_path = sphinx_compas2_theme.get_html_static_path()
html_css_files = []
html_extra_path = []
html_last_updated_fmt = ""
html_copy_source = False
html_show_sourcelink = True
html_permalinks = False
html_permalinks_icon = ""
html_compact_lists = True
