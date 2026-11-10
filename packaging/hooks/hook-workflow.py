"""This repository's workflow.py is not the third-party 'workflow' package.

Override the contrib hook for that unrelated package. Imports in the local
workflow module are discovered normally by PyInstaller's analysis.
"""
