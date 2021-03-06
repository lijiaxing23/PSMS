"""empty message

Revision ID: 9109b878f931
Revises: e56ee4bdbce1
Create Date: 2016-12-22 11:18:54.176695

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9109b878f931'
down_revision = 'e56ee4bdbce1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('offer', sa.Column('customer_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'offer', 'customers', ['customer_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'offer', type_='foreignkey')
    op.drop_column('offer', 'customer_id')
    # ### end Alembic commands ###
