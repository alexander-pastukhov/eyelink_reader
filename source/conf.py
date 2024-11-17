# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../src'))


project = 'eyelink_reader'
copyright = '2024, Alexander (Sasha) Pastukhov'
author = 'Alexander (Sasha) Pastukhov'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_copybutton',
    'numpydoc',
    'myst_parser',
    # 'sphinx.ext.viewcode',  # Optional, adds links to the source code.
    'sphinx.ext.napoleon'  # Ensures compatibility with NumPy and Google docstring formats.
]

templates_path = ['_templates']

exclude_patterns = ["src/eyelink_reader/edfdata.py",
                    "src/eyelink_reader/edfdata_containers.py"]

autodoc_default_options = {
    'private-members': False,
    'special-members': False  # Or True if you need other special members like __init__
}

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
pygments_style = 'sphinx'
