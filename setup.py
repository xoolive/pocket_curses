import os

from setuptools import setup

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'readme.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pocket_curses",
    version="0.1",
    author="Xavier Olive",
    author_email="git@xoolive.org",
    url="https://github.com/xoolive/pocket_curses/",
    description="An ncurses interface to Pocket API",
    long_description=long_description,
    license="MIT",
    packages=["pocket_curses"],
    install_requires=["appdirs", "pocket-api", "pyperclip"],
    entry_points={"console_scripts": ["pocket=pocket_curses:main"]},
    python_requires=">=3.6",
)
