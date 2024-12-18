import sphinx_autosummary_accessors

import xproj

project = "xproj"
copyright = "2024, XProj Developers"
author = "XProj Developers"
# The short X.Y version.
version = xproj.__version__.split("+")[0]
# The full version, including alpha/beta/rc tags.
release = xproj.__version__

# -- General configuration  ----------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autosummary_accessors",
    "myst_nb",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pyproj": ("https://pyproj4.github.io/pyproj/stable/", None),
    "xarray": ("https://docs.xarray.dev/en/latest/", None),
}

source_suffix = [".rst", ".md"]

root_doc = "index"

exclude_patterns = [
    "**.ipynb_checkpoints",
    "build/**.ipynb",
    "build",
]

templates_path = ["_templates", sphinx_autosummary_accessors.templates_path]

highlight_language = "python"

pygments_style = "sphinx"

# -- API reference doc options -------------------------------------------

autodoc_typehints = "none"

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_param = False
napoleon_use_rtype = False
napoleon_preprocess_types = True
napoleon_type_aliases = {
    "sequence": ":term:`sequence`",
    "iterable": ":term:`iterable`",
    "callable": ":py:func:`callable`",
    "dict_like": ":term:`dict-like <mapping>`",
    "dict-like": ":term:`dict-like <mapping>`",
    "path-like": ":term:`path-like <path-like object>`",
    "mapping": ":term:`mapping`",
    "hashable": ":term:`hashable <name>`",
    "file-like": ":term:`file-like <file-like object>`",
    "any": ":py:class:`any <object>`",
    "array_like": ":term:`array_like`",
    "array-like": ":term:`array-like <array_like>`",
    # objects without namespace: xproj
    "CRSIndex": "~xproj.CRSIndex",
    # objects without namespace: xarray
    "DataArray": "~xarray.DataArray",
    "Dataset": "~xarray.Dataset",
    # objects without namespace: pyproj
    "CRS": ":py:class:`~pyproj.CRS`",
}

# -- myst-nb options ------------------------------------------------------

nb_execution_timeout = -1
nb_execution_cache_path = "_build/myst-nb"

# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_book_theme"
html_title = "XProj"

html_theme_options = dict(
    repository_url="https://github.com/benbovy/xproj",
    repository_branch="main",
    path_to_docs="docs",
    use_edit_page_button=True,
    use_repository_button=True,
    use_issues_button=True,
    home_page_in_toc=False,
    announcement="Current development status: experimental, proof-of-concept.",
)

# html_static_path = ["_static"]
htmlhelp_basename = "xprojdoc"
