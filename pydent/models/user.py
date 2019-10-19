"""User, group, and budget models."""
from pydent.base import ModelBase
from pydent.marshaller import add_schema
from pydent.relationships import HasMany
from pydent.relationships import HasManyThrough
from pydent.relationships import HasOne


@add_schema
class User(ModelBase):
    """A User model."""

    fields = dict(
        groups=HasMany("Group", "User"),
        user_budget_associations=HasMany("UserBudgetAssociation", "User"),
        budgets=HasManyThrough("Budget", "UserBudgetAssociation"),
        additional=("name", "id", "login"),
        ignore=("password_digest", "remember_token", "key"),
    )

    def __init__(self):
        pass


@add_schema
class UserBudgetAssociation(ModelBase):
    """An association model between a User and a Budget."""

    fields = dict(budget=HasOne("Budget"), user=HasOne("User"))

    def __init__(self):
        pass


@add_schema
class Membership(ModelBase):
    fields = dict(user=HasOne("User"), group=HasOne("Group"))


@add_schema
class Group(ModelBase):
    """A Group model."""

    pass


@add_schema
class Account(ModelBase):
    """An Account model."""


@add_schema
class Budget(ModelBase):
    """A Budget model."""

    fields = dict(user_budget_associations=HasMany("UserBudgetAssociation", "Budget"))


@add_schema
class Invoice(ModelBase):
    """A Invoice model."""

    pass
