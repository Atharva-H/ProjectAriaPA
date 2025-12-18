"""add_metadata_and_message_type_to_chat_messages

Revision ID: 25fbeb24b679
Revises: e16f4b328361
Create Date: 2025-10-27 16:59:37.930856

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '25fbeb24b679'
down_revision: Union[str, Sequence[str], None] = 'e16f4b328361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add message_metadata JSON field to chat_messages table
    op.add_column('chat_messages', sa.Column('message_metadata', JSON, nullable=True))
    
    # Add message_type field to chat_messages table
    op.add_column('chat_messages', sa.Column('message_type', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('chat_messages', 'message_type')
    op.drop_column('chat_messages', 'message_metadata')
