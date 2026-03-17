"""Create initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-17 18:20:00
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "context_sessions",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", name="contextsessionstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_context_sessions_name"),
        "context_sessions",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_context_sessions_user_id"),
        "context_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "optimization_tasks",
        sa.Column("window_id", sa.String(length=36), nullable=False),
        sa.Column("optimization_type", sa.String(length=100), nullable=False),
        sa.Column("goals", sa.JSON(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "IN_PROGRESS",
                "COMPLETED",
                "FAILED",
                name="optimizationstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("progress", sa.Float(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_optimization_tasks_optimization_type"),
        "optimization_tasks",
        ["optimization_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_optimization_tasks_window_id"),
        "optimization_tasks",
        ["window_id"],
        unique=False,
    )

    op.create_table(
        "prompt_templates",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("variables", sa.JSON(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "COMPLETION",
                "CHAT",
                "INSTRUCT",
                "FEWSHOT",
                "CHAIN_OF_THOUGHT",
                "ROLEPLAY",
                name="templatetype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prompt_templates_category"),
        "prompt_templates",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prompt_templates_created_by"),
        "prompt_templates",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prompt_templates_name"),
        "prompt_templates",
        ["name"],
        unique=False,
    )

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "context_windows",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("token_limit", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["context_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_context_windows_name"),
        "context_windows",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_context_windows_provider"),
        "context_windows",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_context_windows_session_id"),
        "context_windows",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "context_elements",
        sa.Column("window_id", sa.String(length=36), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "SYSTEM",
                "USER",
                "ASSISTANT",
                "TOOL",
                name="contextelementrole",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["window_id"],
            ["context_windows.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_context_elements_role"),
        "context_elements",
        ["role"],
        unique=False,
    )
    op.create_index(
        op.f("ix_context_elements_window_id"),
        "context_elements",
        ["window_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_context_elements_window_id"), table_name="context_elements")
    op.drop_index(op.f("ix_context_elements_role"), table_name="context_elements")
    op.drop_table("context_elements")

    op.drop_index(op.f("ix_context_windows_session_id"), table_name="context_windows")
    op.drop_index(op.f("ix_context_windows_provider"), table_name="context_windows")
    op.drop_index(op.f("ix_context_windows_name"), table_name="context_windows")
    op.drop_table("context_windows")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_prompt_templates_name"), table_name="prompt_templates")
    op.drop_index(op.f("ix_prompt_templates_created_by"), table_name="prompt_templates")
    op.drop_index(op.f("ix_prompt_templates_category"), table_name="prompt_templates")
    op.drop_table("prompt_templates")

    op.drop_index(
        op.f("ix_optimization_tasks_window_id"),
        table_name="optimization_tasks",
    )
    op.drop_index(
        op.f("ix_optimization_tasks_optimization_type"),
        table_name="optimization_tasks",
    )
    op.drop_table("optimization_tasks")

    op.drop_index(op.f("ix_context_sessions_user_id"), table_name="context_sessions")
    op.drop_index(op.f("ix_context_sessions_name"), table_name="context_sessions")
    op.drop_table("context_sessions")
