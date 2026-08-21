"""add lifestyle column

Revision ID: 3243cd8c4388
Revises: c819e9c5b39b
Create Date: 2026-08-07 17:42:35.119002

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '3243cd8c4388'
down_revision: Union[str, Sequence[str], None] = 'c819e9c5b39b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 기존 테이블을 건드리지 않고 'lifestyle' 컬럼만 안전하게 추가합니다.
    op.add_column('users', sa.Column('lifestyle', sa.String(length=255), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'lifestyle')