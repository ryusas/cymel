# -*- coding: utf-8 -*-
"""
Documentation build script for cymel.
Clears old build directories, compiles gettext translations, and builds
both Japanese and English documentation.
"""
from __future__ import absolute_import, print_function, unicode_literals
import os
import shutil
import subprocess
import sys

# Paths are relative to the project root directory
DOCSRC_DIR = 'docsrc'
SRCS_DIR = os.path.join(DOCSRC_DIR, 'srcs')
LOCALE_DIR = os.path.join(DOCSRC_DIR, 'locale')
DOCS_DIR = 'docs'
JA_DIR = os.path.join(DOCS_DIR, 'ja')
EN_DIR = os.path.join(DOCS_DIR, 'en')


def run_command(args):
    print("Running:", " ".join(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            print(output.decode('utf-8', errors='replace').strip())
    rc = process.poll()
    if rc != 0:
        raise RuntimeError("Command failed with exit code {}".format(rc))


def main():
    # 1. Clean previous build directories
    for path in [JA_DIR, EN_DIR]:
        if os.path.exists(path):
            print("Cleaning directory: {}".format(path))
            shutil.rmtree(path)
        os.makedirs(path)

    # 2. Compile PO files to MO files using sphinx-intl
    print("\n--- Compiling translation files ---")
    run_command([
        sys.executable, '-m', 'sphinx_intl', 'build',
        '-d', LOCALE_DIR
    ])

    # 3. Build Japanese documentation
    print("\n--- Building Japanese documentation ---")
    run_command([
        sys.executable, '-m', 'sphinx.cmd.build',
        '-b', 'html',
        SRCS_DIR, JA_DIR
    ])

    # 4. Build English documentation
    print("\n--- Building English documentation ---")
    run_command([
        sys.executable, '-m', 'sphinx.cmd.build',
        '-b', 'html',
        '-D', 'language=en',
        SRCS_DIR, EN_DIR
    ])

    # 5. Create .nojekyll files to bypass GitHub Pages Jekyll processing
    print("\n--- Ensuring .nojekyll files exist ---")
    for path in [DOCS_DIR, JA_DIR, EN_DIR]:
        nojekyll_file = os.path.join(path, '.nojekyll')
        if not os.path.exists(nojekyll_file):
            print("Creating: {}".format(nojekyll_file))
            with open(nojekyll_file, 'wb') as f:
                pass

    print("\nDocumentation built successfully!")


if __name__ == '__main__':
    main()
