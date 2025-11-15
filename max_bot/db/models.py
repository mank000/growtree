from __future__ import annotations

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.BigIntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    goal = fields.CharField(default="Другое", max_length=64)
    chosen_tree = fields.CharField(default="standard_tree", max_length=64)

    tasks: fields.ReverseRelation["Task"]
    trees: fields.ReverseRelation["Tree"]


class Task(Model):
    id = fields.IntField(primary_key=True)
    chosen_days = fields.IntField(default=0)
    name = fields.CharField(max_length=256)
    status = fields.CharField(max_length=20, default="active")
    start_at = fields.DatetimeField(auto_now_add=True)
    end_at = fields.DatetimeField(null=True)
    last_completed_at = fields.DatetimeField(null=True)
    reminder_time = fields.TimeField(null=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="tasks"
    )
    trees: fields.ReverseRelation["Tree"]


class Tree(Model):
    id = fields.IntField(primary_key=True)
    height = fields.IntField(default=0)
    status = fields.CharField(max_length=20, default="alive")
    type_tree = fields.CharField(max_length=30, default="standard_tree")
    planted_at = fields.DatetimeField(auto_now_add=True)

    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="trees"
    )
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        "models.Task",
        related_name="trees",
    )
