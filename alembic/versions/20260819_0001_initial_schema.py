"""Create the workflow and model-serving schema.

Revision ID: 20260819_0001
Revises:
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260819_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role = sa.Enum("ADMIN", "OPERATOR", "VIEWER", name="user_role", native_enum=False)
model_status = sa.Enum("DRAFT", "ACTIVE", "RETIRED", name="model_status", native_enum=False)
job_type = sa.Enum(
    "DATA_PREPARATION",
    "MODEL_INFERENCE",
    "REPORT_GENERATION",
    "FILE_PROCESSING",
    name="job_type",
    native_enum=False,
)
job_status = sa.Enum(
    "QUEUED",
    "RUNNING",
    "RETRYING",
    "SUCCEEDED",
    "FAILED",
    "CANCELLED",
    name="job_status",
    native_enum=False,
)
stage_status = sa.Enum(
    "PENDING",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "SKIPPED",
    name="stage_status",
    native_enum=False,
)
output_kind = sa.Enum(
    "JSON",
    "FILE",
    "REPORT",
    "PREDICTION",
    name="output_kind",
    native_enum=False,
)


def timestamp_columns() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=False),
        sa.Column("artifact_uri", sa.String(length=1000), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("status", model_status, nullable=False),
        sa.Column("model_metadata", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_model_versions_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_versions")),
        sa.UniqueConstraint(
            "name",
            "version",
            name="uq_model_versions_name_version",
        ),
    )
    op.create_index(op.f("ix_model_versions_name"), "model_versions", ["name"])
    op.create_index(op.f("ix_model_versions_status"), "model_versions", ["status"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("model_version_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("job_type", job_type, nullable=False),
        sa.Column("status", job_status, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="priority_range"),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_jobs_model_version_id_model_versions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_jobs_owner_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jobs")),
        sa.UniqueConstraint("task_id", name=op.f("uq_jobs_task_id")),
    )
    op.create_index(op.f("ix_jobs_model_version_id"), "jobs", ["model_version_id"])
    op.create_index(op.f("ix_jobs_owner_id"), "jobs", ["owner_id"])
    op.create_index(op.f("ix_jobs_queued_at"), "jobs", ["queued_at"])
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"])
    op.create_index("ix_jobs_owner_status_created", "jobs", ["owner_id", "status", "created_at"])
    op.create_index("ix_jobs_status_queued", "jobs", ["status", "queued_at"])

    op.create_table(
        "processing_stages",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", stage_status, nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_processing_stages_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_stages")),
        sa.UniqueConstraint(
            "job_id",
            "sequence",
            name="uq_processing_stages_job_sequence",
        ),
    )
    op.create_index(op.f("ix_processing_stages_job_id"), "processing_stages", ["job_id"])
    op.create_index(
        "ix_processing_stages_job_status",
        "processing_stages",
        ["job_id", "status"],
    )

    op.create_table(
        "job_outputs",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("kind", output_kind, nullable=False),
        sa.Column("uri", sa.String(length=1000), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("content_type", sa.String(length=160), nullable=False),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_job_outputs_job_id_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_outputs")),
    )
    op.create_index(op.f("ix_job_outputs_job_id"), "job_outputs", ["job_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("scope", sa.String(length=160), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_idempotency_records")),
        sa.UniqueConstraint(
            "scope",
            "key",
            name="uq_idempotency_records_scope_key",
        ),
    )
    op.create_index(
        "ix_idempotency_records_expires",
        "idempotency_records",
        ["expires_at"],
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        *timestamp_columns(),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=100), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_audit_events_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name=op.f("fk_audit_events_job_id_jobs"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(op.f("ix_audit_events_action"), "audit_events", ["action"])
    op.create_index(op.f("ix_audit_events_actor_id"), "audit_events", ["actor_id"])
    op.create_index(op.f("ix_audit_events_job_id"), "audit_events", ["job_id"])
    op.create_index(op.f("ix_audit_events_request_id"), "audit_events", ["request_id"])
    op.create_index(
        "ix_audit_events_resource_created",
        "audit_events",
        ["resource_type", "resource_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("idempotency_records")
    op.drop_table("job_outputs")
    op.drop_table("processing_stages")
    op.drop_table("jobs")
    op.drop_table("model_versions")
    op.drop_table("users")
