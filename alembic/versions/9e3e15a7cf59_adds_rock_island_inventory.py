"""Adds rock island inventory

Revision ID: 9e3e15a7cf59
Revises: 27a3a3676666
Create Date: 2017-09-23 16:26:14.896484

"""


# revision identifiers, used by Alembic.
revision = '9e3e15a7cf59'
down_revision = '27a3a3676666'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
import sideboard


try:
    is_sqlite = op.get_context().dialect.name == 'sqlite'
except:
    is_sqlite = False

if is_sqlite:
    op.get_context().connection.execute('PRAGMA foreign_keys=ON;')
    utcnow_server_default = "(datetime('now', 'utc'))"
else:
    utcnow_server_default = "timezone('utc', current_timestamp)"

def sqlite_column_reflect_listener(inspector, table, column_info):
    """Adds parenthesis around SQLite datetime defaults for utcnow."""
    if column_info['default'] == "datetime('now', 'utc')":
        column_info['default'] = utcnow_server_default

sqlite_reflect_kwargs = {
    'listeners': [('column_reflect', sqlite_column_reflect_listener)]
}

# ===========================================================================
# HOWTO: Handle alter statements in SQLite
#
# def upgrade():
#     if is_sqlite:
#         with op.batch_alter_table('table_name', reflect_kwargs=sqlite_reflect_kwargs) as batch_op:
#             batch_op.alter_column('column_name', type_=sa.Unicode(), server_default='', nullable=False)
#     else:
#         op.alter_column('table_name', 'column_name', type_=sa.Unicode(), server_default='', nullable=False)
#
# ===========================================================================


def upgrade():
    # Leftover renaming from the bands -> guests refactor
    op.create_unique_constraint(op.f('uq_guest_bio_guest_id'), 'guest_bio', ['guest_id'])
    op.drop_constraint('uq_band_bio_band_id', 'guest_bio', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_charity_guest_id'), 'guest_charity', ['guest_id'])
    op.drop_constraint('uq_band_charity_band_id', 'guest_charity', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_info_guest_id'), 'guest_info', ['guest_id'])
    op.drop_constraint('uq_band_info_band_id', 'guest_info', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_merch_guest_id'), 'guest_merch', ['guest_id'])
    op.drop_constraint('uq_band_merch_band_id', 'guest_merch', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_panel_guest_id'), 'guest_panel', ['guest_id'])
    op.drop_constraint('uq_band_panel_band_id', 'guest_panel', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_stage_plot_guest_id'), 'guest_stage_plot', ['guest_id'])
    op.drop_constraint('uq_band_stage_plot_band_id', 'guest_stage_plot', type_='unique')
    op.create_unique_constraint(op.f('uq_guest_taxes_guest_id'), 'guest_taxes', ['guest_id'])
    op.drop_constraint('uq_band_taxes_band_id', 'guest_taxes', type_='unique')

    op.add_column('guest_merch', sa.Column('bringing_boxes', sa.Unicode(), server_default='', nullable=False))
    op.add_column('guest_merch', sa.Column('extra_info', sa.Unicode(), server_default='', nullable=False))
    op.add_column('guest_merch', sa.Column('inventory', sideboard.lib.sa.JSON(), server_default='[]', nullable=False))


def downgrade():
    op.create_unique_constraint('uq_band_taxes_band_id', 'guest_taxes', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_taxes_guest_id'), 'guest_taxes', type_='unique')
    op.create_unique_constraint('uq_band_stage_plot_band_id', 'guest_stage_plot', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_stage_plot_guest_id'), 'guest_stage_plot', type_='unique')
    op.create_unique_constraint('uq_band_panel_band_id', 'guest_panel', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_panel_guest_id'), 'guest_panel', type_='unique')
    op.create_unique_constraint('uq_band_merch_band_id', 'guest_merch', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_merch_guest_id'), 'guest_merch', type_='unique')
    op.create_unique_constraint('uq_band_info_band_id', 'guest_info', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_info_guest_id'), 'guest_info', type_='unique')
    op.create_unique_constraint('uq_band_charity_band_id', 'guest_charity', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_charity_guest_id'), 'guest_charity', type_='unique')
    op.create_unique_constraint('uq_band_bio_band_id', 'guest_bio', ['guest_id'])
    op.drop_constraint(op.f('uq_guest_bio_guest_id'), 'guest_bio', type_='unique')

    op.drop_column('guest_merch', 'inventory')
    op.drop_column('guest_merch', 'extra_info')
    op.drop_column('guest_merch', 'bringing_boxes')
