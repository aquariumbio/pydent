Installing Trident
==================

Installing Trident is easy. You'll need ``Python3.7`` and ``pip3``.

You can install or upgrade Trident from the PyPI repository using:

.. code-block::

    pip3 install pydent -U

If you need to install a specific version, you can run:

.. code-block:: cmd

    pip3 install pydent==0.1.0-apha -U

Thats it!

Installation for developers
---------------------------

You can pull the git repo from
`here <https://github.com/klavinslab/trident>`__.

To install the trident dependencies in a virual environment, you first
need `poetry <https://poetry.eustace.io/>`__, which can generally be
installed with the following:

.. code-block::

    curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
    source $HOME/.poetry/env

Finally, once you ``cd`` into the trident directory, simply run

.. code-block::

    poetry install

which will install the dependencies in your virtual environement (or
create a new one if you are not in a virtual environment).

From there, you can run the normal command from within the environment
using:

.. code-block::

    poetry run [command]

Such as running pytest:

.. code-block::

    poetry run pytest tests

Or you can opening a virtual env shell:

.. code-block::

    poetry shell
