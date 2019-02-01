An ncurses interface to Pocket API
==================================

Usage
-----

::

  pocket

Press `?` for help, `q` to quit.

The interface is based on the `pocket-api` library which requires an API key. The following `page <https://github.com/rakanalh/pocket-api#usage>`_ explains how to create one.

When you first launch `pocket`, a configuration file is created. An exception is raised until you put your credentials in the file. The exception message contains the path to the configuration file.

Installation
------------

This tool requires Python>=3.6.

Latest release:

::

  pip3 install pocket-curses

  # in case you don't have sufficient permissions
  pip3 install pocket-curses --user


Latest version from github:

::

  pip3 install git+https://github.com/xoolive/pocket_curses

License
-------

MIT

All contributions welcome.
