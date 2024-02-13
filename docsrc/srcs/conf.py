# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('../python'))
sys.path.insert(0, os.path.abspath('../../python'))

import cymel
import mayaconf
import datetime


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'cymel'
copyright = '2020-%d, ryusas' % (datetime.date.today().year,)
author = 'ryusas'
release = cymel.__version__


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    #'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',

    'sphinx.ext.inheritance_diagram',
    #'sphinx.ext.graphviz',
    'sphinx.ext.extlinks',
]

templates_path = ['../templates']
exclude_patterns = [u'_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'sphinxdoc'
#html_theme_options = {}

html_static_path = ['../static']


# -----------------------------------------------------------------------
default_role = 'py:obj'  # autodoc されたドキュメント内へのリンクを簡単に書くために重要。

#source_suffix = ['.rst', '.md']
source_suffix = '.rst'

language = 'ja'

#gettext_compact = False

pygments_style = 'sphinx'


mayaconf.set_all_filters()
extlinks = mayaconf.get_std_extlinks()

autoclass_content = 'both'  # 'class', 'both', 'init'
autosummary_generate = True
#autodoc_default_flags = ['members', 'undoc-members', 'show-inheritance']
#keep_warnings = True

inheritance_graph_attrs = dict(rankdir="TB", nodesep=0.15, ranksep=0.15)
                            #, size='"6.0, 8.0"',
                            #   fontsize=14, ratio='compress')
inheritance_node_attrs = dict(fontsize=8)

intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

todo_include_todos = True


# -------------------------
def setup(app):
    print('SETUP====================================')
    app.add_css_file('custom.css')

