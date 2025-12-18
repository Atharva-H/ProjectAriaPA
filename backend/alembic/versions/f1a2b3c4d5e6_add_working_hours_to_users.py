"""add_working_hours_to_users

Revision ID: f1a2b3c4d5e6
Revises: 25fbeb24b679
Create Date: 2025-10-27 18:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '25fbeb24b679'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add working hours fields to users table
    op.add_column('users', sa.Column('working_hours_start', sa.Integer(), nullable=True, server_default='9'))
    op.add_column('users', sa.Column('working_hours_end', sa.Integer(), nullable=True, server_default='18'))
    op.add_column('users', sa.Column('working_days', JSON, nullable=True, server_default='["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('users', 'working_days')
    op.drop_column('users', 'working_hours_end')
    op.drop_column('users', 'working_hours_start')
