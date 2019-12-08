"""
Planner (:mod:`pydent.planner`)
===============================

.. versionadded:: 0.1
    Planning module created

.. currentmodule:: pydent.planner

The planner module allows users to plan and submit simple and complex scientific
experiments and upload the plan to the Aquarium server for execution.

.. seealso::
    For more information on how to plan experiments using Trident,
    see :ref:`Planning Docs <planning>` and the :ref:`Advanced Topics <advancedtopics>`.

Classes
-------

.. autosummary::
    :toctree: generated/

    Planner
    PlannerLayout

Exceptions
----------

.. autosummary::
    :toctree: generated/

    PlannerException
"""
from pydent.planner.graph import PlannerLayout
from pydent.planner.planner import Planner
from pydent.planner.planner import PlannerException
