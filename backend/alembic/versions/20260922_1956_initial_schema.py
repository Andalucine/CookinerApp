"""initial schema (v2: personal notebook, catalogs, pantry, shopping list, notes, favorites,
notebook blends, notebook spices and substitutions)

Revision ID: 0002a1b2c3d4
Revises:
Create Date: 2026-09-22 19:56:50.076614

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002a1b2c3d4"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=10), nullable=False),
        sa.Column("name_es", sa.String(length=50), nullable=False),
        sa.Column("name_en", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_seasons")),
        sa.UniqueConstraint("code", name=op.f("uq_seasons_code")),
    )
    op.create_table(
        "shopping_sections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name_es", sa.String(length=60), nullable=False),
        sa.Column("name_en", sa.String(length=60), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopping_sections")),
        sa.UniqueConstraint("code", name=op.f("uq_shopping_sections_code")),
    )
    op.create_table(
        "spice_equivalence_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("situation_es", sa.String(length=120), nullable=False),
        sa.Column("situation_en", sa.String(length=120), nullable=False),
        sa.Column("equivalence_es", sa.String(length=200), nullable=False),
        sa.Column("equivalence_en", sa.String(length=200), nullable=False),
        sa.Column("note_es", sa.String(length=200), nullable=True),
        sa.Column("note_en", sa.String(length=200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spice_equivalence_rules")),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name_es", sa.String(length=60), nullable=False),
        sa.Column("name_en", sa.String(length=60), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tags")),
        sa.UniqueConstraint("kind", "code", name=op.f("uq_tags_kind_code")),
    )
    op.create_index(op.f("ix_tags_kind"), "tags", ["kind"], unique=False)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("language", sa.String(length=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("plan", sa.String(length=20), nullable=False),
        sa.Column("max_recipes", sa.Integer(), nullable=True),
        sa.Column("max_shared_with", sa.Integer(), nullable=True),
        sa.Column("family_owner_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["family_owner_id"],
            ["users.id"],
            name=op.f("fk_users_family_owner_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_table(
        "wine_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("name_es", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80), nullable=False),
        sa.Column("examples_es", sa.String(length=200), nullable=True),
        sa.Column("serving_temp", sa.String(length=20), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["wine_categories.id"],
            name=op.f("fk_wine_categories_parent_id_wine_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wine_categories")),
        sa.UniqueConstraint("parent_id", "slug", name=op.f("uq_wine_categories_parent_id_slug")),
    )
    op.create_index(
        op.f("ix_wine_categories_parent_id"), "wine_categories", ["parent_id"], unique=False
    )
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_identities_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_identities")),
        sa.UniqueConstraint(
            "provider",
            "provider_user_id",
            name=op.f("uq_auth_identities_provider_provider_user_id"),
        ),
    )
    op.create_index(
        op.f("ix_auth_identities_user_id"), "auth_identities", ["user_id"], unique=False
    )
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_en", sa.String(length=100), nullable=True),
        sa.Column("aliases", sa.String(length=300), nullable=True),
        sa.Column("is_spice", sa.Boolean(), nullable=False),
        sa.Column("spice_family", sa.String(length=30), nullable=True),
        sa.Column("shopping_section_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["shopping_section_id"],
            ["shopping_sections.id"],
            name=op.f("fk_ingredients_shopping_section_id_shopping_sections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingredients")),
    )
    op.create_index(op.f("ix_ingredients_name"), "ingredients", ["name"], unique=True)
    op.create_table(
        "notebooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_notebooks_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebooks")),
        sa.UniqueConstraint("owner_id", name=op.f("uq_notebooks_owner_id")),
    )
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_password_reset_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_reset_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_password_reset_tokens_token_hash")),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"], unique=False
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("notebook_id", sa.Integer(), nullable=True),
        sa.Column("slug", sa.String(length=60), nullable=False),
        sa.Column("name_es", sa.String(length=80), nullable=False),
        sa.Column("name_en", sa.String(length=80), nullable=False),
        sa.Column("examples_es", sa.String(length=200), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("is_preloaded", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_categories_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name=op.f("fk_categories_parent_id_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("parent_id", "slug", name=op.f("uq_categories_parent_id_slug")),
    )
    op.create_index(op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False)
    op.create_table(
        "notebook_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notebook_access_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_notebook_access_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_access")),
        sa.UniqueConstraint(
            "notebook_id", "user_id", name=op.f("uq_notebook_access_notebook_id_user_id")
        ),
    )
    op.create_index(
        op.f("ix_notebook_access_notebook_id"), "notebook_access", ["notebook_id"], unique=False
    )
    op.create_index(
        op.f("ix_notebook_access_user_id"), "notebook_access", ["user_id"], unique=False
    )
    op.create_table(
        "notebook_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("invited_by_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_id"],
            ["users.id"],
            name=op.f("fk_notebook_invitations_accepted_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_id"],
            ["users.id"],
            name=op.f("fk_notebook_invitations_invited_by_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notebook_invitations_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_invitations")),
        sa.UniqueConstraint("code", name=op.f("uq_notebook_invitations_code")),
    )
    op.create_index(
        op.f("ix_notebook_invitations_notebook_id"),
        "notebook_invitations",
        ["notebook_id"],
        unique=False,
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["author_id"], ["users.id"], name=op.f("fk_notes_author_id_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notes_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["users.id"],
            name=op.f("fk_notes_updated_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
    )
    op.create_index(op.f("ix_notes_notebook_id"), "notes", ["notebook_id"], unique=False)
    op.create_table(
        "notebook_blends",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(length=200), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_notebook_blends_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_notebook_blends_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notebook_blends_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_blends")),
        sa.UniqueConstraint(
            "notebook_id",
            "ingredient_id",
            name=op.f("uq_notebook_blends_notebook_id_ingredient_id"),
        ),
    )
    op.create_index(
        op.f("ix_notebook_blends_ingredient_id"), "notebook_blends", ["ingredient_id"], unique=False
    )
    op.create_index(
        op.f("ix_notebook_blends_notebook_id"), "notebook_blends", ["notebook_id"], unique=False
    )
    op.create_table(
        "notebook_blend_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("blend_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("parts", sa.String(length=10), nullable=False),
        sa.Column("is_optional", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["blend_id"],
            ["notebook_blends.id"],
            name=op.f("fk_notebook_blend_items_blend_id_notebook_blends"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_notebook_blend_items_ingredient_id_ingredients"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_blend_items")),
        sa.UniqueConstraint(
            "blend_id", "ingredient_id", name=op.f("uq_notebook_blend_items_blend_id_ingredient_id")
        ),
    )
    op.create_index(
        op.f("ix_notebook_blend_items_blend_id"), "notebook_blend_items", ["blend_id"], unique=False
    )
    op.create_table(
        "notebook_spices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("family", sa.String(length=30), nullable=False),
        sa.Column("aliases", sa.String(length=300), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_notebook_spices_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_notebook_spices_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notebook_spices_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_spices")),
        sa.UniqueConstraint(
            "notebook_id",
            "ingredient_id",
            name=op.f("uq_notebook_spices_notebook_id_ingredient_id"),
        ),
    )
    op.create_index(
        op.f("ix_notebook_spices_ingredient_id"), "notebook_spices", ["ingredient_id"], unique=False
    )
    op.create_index(
        op.f("ix_notebook_spices_notebook_id"), "notebook_spices", ["notebook_id"], unique=False
    )
    op.create_table(
        "notebook_substitutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("substitute", sa.String(length=150), nullable=False),
        sa.Column("substitute_id", sa.Integer(), nullable=True),
        sa.Column("ratio", sa.String(length=60), nullable=True),
        sa.Column("note", sa.String(length=200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_notebook_substitutions_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_notebook_substitutions_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_notebook_substitutions_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["substitute_id"],
            ["ingredients.id"],
            name=op.f("fk_notebook_substitutions_substitute_id_ingredients"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notebook_substitutions")),
    )
    op.create_index(
        op.f("ix_notebook_substitutions_ingredient_id"),
        "notebook_substitutions",
        ["ingredient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notebook_substitutions_notebook_id"),
        "notebook_substitutions",
        ["notebook_id"],
        unique=False,
    )
    op.create_table(
        "occasions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=True),
        sa.Column("name_es", sa.String(length=50), nullable=False),
        sa.Column("name_en", sa.String(length=50), nullable=False),
        sa.Column("is_preloaded", sa.Boolean(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by_id"],
            ["users.id"],
            name=op.f("fk_occasions_created_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_occasions_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_occasions")),
        sa.UniqueConstraint(
            "notebook_id", "name_es", name=op.f("uq_occasions_notebook_id_name_es")
        ),
    )
    op.create_table(
        "pantry_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=10), nullable=True),
        sa.Column(
            "added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_pantry_items_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_pantry_items_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pantry_items")),
        sa.UniqueConstraint(
            "notebook_id", "ingredient_id", name=op.f("uq_pantry_items_notebook_id_ingredient_id")
        ),
    )
    op.create_index(
        op.f("ix_pantry_items_notebook_id"), "pantry_items", ["notebook_id"], unique=False
    )
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=True),
        sa.Column("servings", sa.Integer(), nullable=True),
        sa.Column("cook_name", sa.String(length=100), nullable=True),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("youtube_url", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("language", sa.String(length=2), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.id"],
            name=op.f("fk_recipes_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_recipes_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipes")),
    )
    op.create_index(op.f("ix_recipes_author_id"), "recipes", ["author_id"], unique=False)
    op.create_index(op.f("ix_recipes_notebook_id"), "recipes", ["notebook_id"], unique=False)
    op.create_table(
        "spice_blends",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quick_substitute_es", sa.String(length=150), nullable=True),
        sa.Column("quick_substitute_en", sa.String(length=150), nullable=True),
        sa.Column("note_es", sa.String(length=200), nullable=True),
        sa.Column("note_en", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_spice_blends_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spice_blends")),
        sa.UniqueConstraint("ingredient_id", name=op.f("uq_spice_blends_ingredient_id")),
    )
    op.create_table(
        "spice_substitutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("substitute_es", sa.String(length=150), nullable=False),
        sa.Column("substitute_en", sa.String(length=150), nullable=False),
        sa.Column("substitute_id", sa.Integer(), nullable=True),
        sa.Column("ratio", sa.String(length=60), nullable=True),
        sa.Column("note_es", sa.String(length=200), nullable=True),
        sa.Column("note_en", sa.String(length=200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_spice_substitutions_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["substitute_id"],
            ["ingredients.id"],
            name=op.f("fk_spice_substitutions_substitute_id_ingredients"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spice_substitutions")),
    )
    op.create_index(
        op.f("ix_spice_substitutions_ingredient_id"),
        "spice_substitutions",
        ["ingredient_id"],
        unique=False,
    )
    op.create_table(
        "wines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("winery", sa.String(length=200), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("sweetness", sa.String(length=20), nullable=True),
        sa.Column("body", sa.String(length=10), nullable=True),
        sa.Column("ageing", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=60), nullable=True),
        sa.Column("appellation", sa.String(length=100), nullable=True),
        sa.Column("grapes", sa.String(length=200), nullable=True),
        sa.Column("vintage", sa.Integer(), nullable=True),
        sa.Column("price_range", sa.String(length=4), nullable=True),
        sa.Column("tasting_notes", sa.Text(), nullable=True),
        sa.Column("pairing_notes", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
            name=op.f("fk_wines_added_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["wine_categories.id"],
            name=op.f("fk_wines_category_id_wine_categories"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_wines_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["users.id"],
            name=op.f("fk_wines_updated_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wines")),
    )
    op.create_index(op.f("ix_wines_name"), "wines", ["name"], unique=False)
    op.create_index(op.f("ix_wines_notebook_id"), "wines", ["notebook_id"], unique=False)
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("wine_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(recipe_id IS NOT NULL) <> (wine_id IS NOT NULL)",
            name=op.f("ck_favorites_favorite_recipe_or_wine"),
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_favorites_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_favorites_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["wine_id"], ["wines.id"], name=op.f("fk_favorites_wine_id_wines"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favorites")),
        sa.UniqueConstraint("user_id", "recipe_id", name=op.f("uq_favorites_user_id_recipe_id")),
        sa.UniqueConstraint("user_id", "wine_id", name=op.f("uq_favorites_user_id_wine_id")),
    )
    op.create_index(op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False)
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("wine_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_import_jobs_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_import_jobs_recipe_id_recipes"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_import_jobs_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["wine_id"],
            ["wines.id"],
            name=op.f("fk_import_jobs_wine_id_wines"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_jobs")),
    )
    op.create_index(op.f("ix_import_jobs_user_id"), "import_jobs", ["user_id"], unique=False)
    op.create_table(
        "pairing_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_category_id", sa.Integer(), nullable=False),
        sa.Column("wine_category_id", sa.Integer(), nullable=False),
        sa.Column("reason_es", sa.String(length=200), nullable=False),
        sa.Column("reason_en", sa.String(length=200), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipe_category_id"],
            ["categories.id"],
            name=op.f("fk_pairing_rules_recipe_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wine_category_id"],
            ["wine_categories.id"],
            name=op.f("fk_pairing_rules_wine_category_id_wine_categories"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pairing_rules")),
        sa.UniqueConstraint(
            "recipe_category_id",
            "wine_category_id",
            name=op.f("uq_pairing_rules_recipe_category_id_wine_category_id"),
        ),
    )
    op.create_index(
        op.f("ix_pairing_rules_recipe_category_id"),
        "pairing_rules",
        ["recipe_category_id"],
        unique=False,
    )
    op.create_table(
        "recipe_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_recipe_categories_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_categories_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_categories")),
        sa.UniqueConstraint(
            "recipe_id", "category_id", name=op.f("uq_recipe_categories_recipe_id_category_id")
        ),
    )
    op.create_index(
        op.f("ix_recipe_categories_category_id"), "recipe_categories", ["category_id"], unique=False
    )
    op.create_index(
        op.f("ix_recipe_categories_recipe_id"), "recipe_categories", ["recipe_id"], unique=False
    )
    op.create_table(
        "recipe_contributions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("field", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_contributions_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_recipe_contributions_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_contributions")),
    )
    op.create_index(
        op.f("ix_recipe_contributions_recipe_id"),
        "recipe_contributions",
        ["recipe_id"],
        unique=False,
    )
    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("raw_text", sa.String(length=200), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_recipe_ingredients_ingredient_id_ingredients"),
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_ingredients_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_ingredients")),
    )
    op.create_index(
        op.f("ix_recipe_ingredients_ingredient_id"),
        "recipe_ingredients",
        ["ingredient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recipe_ingredients_recipe_id"), "recipe_ingredients", ["recipe_id"], unique=False
    )
    op.create_table(
        "recipe_occasions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("occasion_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["occasion_id"],
            ["occasions.id"],
            name=op.f("fk_recipe_occasions_occasion_id_occasions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_occasions_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_occasions")),
        sa.UniqueConstraint(
            "recipe_id", "occasion_id", name=op.f("uq_recipe_occasions_recipe_id_occasion_id")
        ),
    )
    op.create_table(
        "recipe_seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_seasons_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["season_id"], ["seasons.id"], name=op.f("fk_recipe_seasons_season_id_seasons")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_seasons")),
        sa.UniqueConstraint(
            "recipe_id", "season_id", name=op.f("uq_recipe_seasons_recipe_id_season_id")
        ),
    )
    op.create_table(
        "recipe_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_tags_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], name=op.f("fk_recipe_tags_tag_id_tags"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_tags")),
        sa.UniqueConstraint("recipe_id", "tag_id", name=op.f("uq_recipe_tags_recipe_id_tag_id")),
    )
    op.create_index(op.f("ix_recipe_tags_tag_id"), "recipe_tags", ["tag_id"], unique=False)
    op.create_table(
        "recipe_wines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("wine_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("origin", sa.String(length=10), nullable=False),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
            name=op.f("fk_recipe_wines_added_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_wines_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["wine_id"],
            ["wines.id"],
            name=op.f("fk_recipe_wines_wine_id_wines"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_wines")),
        sa.UniqueConstraint("recipe_id", "wine_id", name=op.f("uq_recipe_wines_recipe_id_wine_id")),
    )
    op.create_index(op.f("ix_recipe_wines_recipe_id"), "recipe_wines", ["recipe_id"], unique=False)
    op.create_index(op.f("ix_recipe_wines_wine_id"), "recipe_wines", ["wine_id"], unique=False)
    op.create_table(
        "shopping_list_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notebook_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.String(length=50), nullable=True),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("is_checked", sa.Boolean(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=True),
        sa.Column("added_by_id", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["added_by_id"],
            ["users.id"],
            name=op.f("fk_shopping_list_items_added_by_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_shopping_list_items_ingredient_id_ingredients"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
            name=op.f("fk_shopping_list_items_notebook_id_notebooks"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_shopping_list_items_recipe_id_recipes"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["shopping_sections.id"],
            name=op.f("fk_shopping_list_items_section_id_shopping_sections"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shopping_list_items")),
    )
    op.create_index(
        op.f("ix_shopping_list_items_notebook_id"),
        "shopping_list_items",
        ["notebook_id"],
        unique=False,
    )
    op.create_table(
        "spice_blend_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("blend_id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("parts", sa.String(length=10), nullable=False),
        sa.Column("is_optional", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["blend_id"],
            ["spice_blends.id"],
            name=op.f("fk_spice_blend_items_blend_id_spice_blends"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_spice_blend_items_ingredient_id_ingredients"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_spice_blend_items")),
        sa.UniqueConstraint(
            "blend_id", "ingredient_id", name=op.f("uq_spice_blend_items_blend_id_ingredient_id")
        ),
    )
    op.create_index(
        op.f("ix_spice_blend_items_blend_id"), "spice_blend_items", ["blend_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("notebook_substitutions")
    op.drop_table("notebook_spices")
    op.drop_table("notebook_blend_items")
    op.drop_table("notebook_blends")
    op.drop_index(op.f("ix_spice_blend_items_blend_id"), table_name="spice_blend_items")
    op.drop_table("spice_blend_items")
    op.drop_index(op.f("ix_shopping_list_items_notebook_id"), table_name="shopping_list_items")
    op.drop_table("shopping_list_items")
    op.drop_index(op.f("ix_recipe_wines_wine_id"), table_name="recipe_wines")
    op.drop_index(op.f("ix_recipe_wines_recipe_id"), table_name="recipe_wines")
    op.drop_table("recipe_wines")
    op.drop_index(op.f("ix_recipe_tags_tag_id"), table_name="recipe_tags")
    op.drop_table("recipe_tags")
    op.drop_table("recipe_seasons")
    op.drop_table("recipe_occasions")
    op.drop_index(op.f("ix_recipe_ingredients_recipe_id"), table_name="recipe_ingredients")
    op.drop_index(op.f("ix_recipe_ingredients_ingredient_id"), table_name="recipe_ingredients")
    op.drop_table("recipe_ingredients")
    op.drop_index(op.f("ix_recipe_contributions_recipe_id"), table_name="recipe_contributions")
    op.drop_table("recipe_contributions")
    op.drop_index(op.f("ix_recipe_categories_recipe_id"), table_name="recipe_categories")
    op.drop_index(op.f("ix_recipe_categories_category_id"), table_name="recipe_categories")
    op.drop_table("recipe_categories")
    op.drop_index(op.f("ix_pairing_rules_recipe_category_id"), table_name="pairing_rules")
    op.drop_table("pairing_rules")
    op.drop_index(op.f("ix_import_jobs_user_id"), table_name="import_jobs")
    op.drop_table("import_jobs")
    op.drop_index(op.f("ix_favorites_user_id"), table_name="favorites")
    op.drop_table("favorites")
    op.drop_index(op.f("ix_wines_notebook_id"), table_name="wines")
    op.drop_index(op.f("ix_wines_name"), table_name="wines")
    op.drop_table("wines")
    op.drop_index(op.f("ix_spice_substitutions_ingredient_id"), table_name="spice_substitutions")
    op.drop_table("spice_substitutions")
    op.drop_table("spice_blends")
    op.drop_index(op.f("ix_recipes_notebook_id"), table_name="recipes")
    op.drop_index(op.f("ix_recipes_author_id"), table_name="recipes")
    op.drop_table("recipes")
    op.drop_index(op.f("ix_pantry_items_notebook_id"), table_name="pantry_items")
    op.drop_table("pantry_items")
    op.drop_table("occasions")
    op.drop_index(op.f("ix_notes_notebook_id"), table_name="notes")
    op.drop_table("notes")
    op.drop_index(op.f("ix_notebook_invitations_notebook_id"), table_name="notebook_invitations")
    op.drop_table("notebook_invitations")
    op.drop_index(op.f("ix_notebook_access_user_id"), table_name="notebook_access")
    op.drop_index(op.f("ix_notebook_access_notebook_id"), table_name="notebook_access")
    op.drop_table("notebook_access")
    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_table("categories")
    op.drop_index(op.f("ix_password_reset_tokens_user_id"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("notebooks")
    op.drop_index(op.f("ix_ingredients_name"), table_name="ingredients")
    op.drop_table("ingredients")
    op.drop_index(op.f("ix_auth_identities_user_id"), table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_index(op.f("ix_wine_categories_parent_id"), table_name="wine_categories")
    op.drop_table("wine_categories")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_tags_kind"), table_name="tags")
    op.drop_table("tags")
    op.drop_table("spice_equivalence_rules")
    op.drop_table("shopping_sections")
    op.drop_table("seasons")
