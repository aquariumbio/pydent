Creating and updating documentation
===================================

Most functions, classes and modules are documented in the code. Try to
maintain the same style of documentation as:

.. code:: python

        def __init__(self, aqhttp, session):
            """
            Initializer for SessionInterface

            :param aqhttp: aqhttp instance for this interface
            :type aqhttp: AqHTTP
            :param session: session instance for this interface
            :type session: AqSession
            """
            self.aqhttp = aqhttp
            self.session = session

These docstrings are parsed and used by Sphinx to create the
documentation website.

Updating sphinx documentation
-----------------------------

To convert .md files located in the trident folder to .rst file
(required by Sphinx), run:

.. code:: bash

    ./ scripts/convert_md_to_rst.sh

Following that, to update
