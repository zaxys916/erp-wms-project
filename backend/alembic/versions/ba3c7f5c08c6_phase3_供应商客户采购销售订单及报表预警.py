"""phase3 供应商客户采购销售订单及报表预警

Revision ID: ba3c7f5c08c6
Revises: ca00186e886e
Create Date: 2026-09-08 21:17:07.057122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba3c7f5c08c6'
down_revision: Union[str, Sequence[str], None] = 'ca00186e886e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # products 扩展安全库存与价格字段（存量行默认 0）
    op.add_column('products', sa.Column('safety_stock', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('products', sa.Column('price', sa.Numeric(12, 2), nullable=False, server_default='0'))
    op.add_column('products', sa.Column('cost', sa.Numeric(12, 2), nullable=False, server_default='0'))

    # 供应商 / 客户档案
    op.create_table('suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('contact', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_suppliers'),
        sa.UniqueConstraint('name', name='uq_suppliers_name'),
    )
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('contact', sa.String(length=50), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name='pk_customers'),
        sa.UniqueConstraint('name', name='uq_customers_name'),
    )

    # 采购订单 + 明细
    op.create_table('purchase_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(length=30), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('remark', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ),
        sa.PrimaryKeyConstraint('id', name='pk_purchase_orders'),
        sa.UniqueConstraint('order_no', name='uq_purchase_orders_order_no'),
    )
    op.create_index(op.f('ix_purchase_orders_created_at'), 'purchase_orders', ['created_at'], unique=False)
    op.create_index(op.f('ix_purchase_orders_order_no'), 'purchase_orders', ['order_no'], unique=True)
    op.create_index(op.f('ix_purchase_orders_supplier_id'), 'purchase_orders', ['supplier_id'], unique=False)

    op.create_table('purchase_order_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('purchase_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ),
        sa.PrimaryKeyConstraint('id', name='pk_purchase_order_item'),
    )
    op.create_index(op.f('ix_purchase_order_item_product_id'), 'purchase_order_item', ['product_id'], unique=False)
    op.create_index(op.f('ix_purchase_order_item_purchase_order_id'), 'purchase_order_item', ['purchase_order_id'], unique=False)

    # 销售订单 + 明细
    op.create_table('sale_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(length=30), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('remark', sa.String(length=255), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('shipped_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id', name='pk_sale_orders'),
        sa.UniqueConstraint('order_no', name='uq_sale_orders_order_no'),
    )
    op.create_index(op.f('ix_sale_orders_created_at'), 'sale_orders', ['created_at'], unique=False)
    op.create_index(op.f('ix_sale_orders_customer_id'), 'sale_orders', ['customer_id'], unique=False)
    op.create_index(op.f('ix_sale_orders_order_no'), 'sale_orders', ['order_no'], unique=True)

    op.create_table('sale_order_item',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sale_order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 2), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['sale_order_id'], ['sale_orders.id'], ),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ),
        sa.PrimaryKeyConstraint('id', name='pk_sale_order_item'),
    )
    op.create_index(op.f('ix_sale_order_item_product_id'), 'sale_order_item', ['product_id'], unique=False)
    op.create_index(op.f('ix_sale_order_item_sale_order_id'), 'sale_order_item', ['sale_order_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_sale_order_item_sale_order_id'), table_name='sale_order_item')
    op.drop_index(op.f('ix_sale_order_item_product_id'), table_name='sale_order_item')
    op.drop_table('sale_order_item')
    op.drop_index(op.f('ix_sale_orders_order_no'), table_name='sale_orders')
    op.drop_index(op.f('ix_sale_orders_customer_id'), table_name='sale_orders')
    op.drop_index(op.f('ix_sale_orders_created_at'), table_name='sale_orders')
    op.drop_table('sale_orders')
    op.drop_index(op.f('ix_purchase_order_item_purchase_order_id'), table_name='purchase_order_item')
    op.drop_index(op.f('ix_purchase_order_item_product_id'), table_name='purchase_order_item')
    op.drop_table('purchase_order_item')
    op.drop_index(op.f('ix_purchase_orders_supplier_id'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_order_no'), table_name='purchase_orders')
    op.drop_index(op.f('ix_purchase_orders_created_at'), table_name='purchase_orders')
    op.drop_table('purchase_orders')
    op.drop_table('customers')
    op.drop_table('suppliers')
    op.drop_column('products', 'cost')
    op.drop_column('products', 'price')
    op.drop_column('products', 'safety_stock')
