Installation
============

Requirements
------------

-  python3.6
-  pip

pipenv installation (recommended)
---------------------------------

It is recommended you install Trident using pipenv.
`Pipenv <https://docs.pipenv.org/>`__ is now the officially
recommended Python packaging tool from Python.org. It will install
packages on a *per project basis* by creating a virtualenv for your
package containing all of trident's necessary dependencies.

Alternatively, **pip** can be used, which is probably the easiest way to
install python packages (see "pip installation" below).

pipenv trident installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To install trident, download trident from github, move into trident's
root directory and run:

::

    make

That's it. You'll be able to install pydent to your projects (see below)

pipenv trident environment
~~~~~~~~~~~~~~~~~~~~~~~~~~

To open the environment containing all of trident's dependencies, run

::

    cd path/to/trident
    pipenv shell

You can run any terminal command in trident's environment using

::

    pipenv run [command]

To run a python interpreter

::

    cd path/to/trident
    pipenv run python

..and from there you can import trident

.. code:: python

    import pydent

    # stuff with trident/pydent

pip installation (easiest)
--------------------------

**Pip** will, for the most part, install packages *globally.* To install
trident using pip, simply move into trident's root directory and run:

::

    pip install . --upgrade

You will than be able to access trident in your python interpreter via:

.. code:: python

    import pydent

installing trident from remote
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As soon as we create an official release, trident can be installed from
remote via git using:

::

    pipenv install git+https://github.com/klavinslab/trident.git@VER#egg=pydent
