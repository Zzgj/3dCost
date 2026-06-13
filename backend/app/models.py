from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# 金额：Numeric(10,4)；数量：Numeric(12,3)
AMOUNT = Numeric(10, 4)
QTY = Numeric(12, 3)


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(50), default="")
    brand: Mapped[str] = mapped_column(String(100), default="")
    stock_g: Mapped[Decimal] = mapped_column(QTY, default=Decimal("0"))
    low_stock_g: Mapped[Decimal] = mapped_column(QTY, default=Decimal("0"))
    avg_price_per_g: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Supplier(Base):
    __tablename__ = "suppliers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), default="")
    spec: Mapped[str] = mapped_column(String(200), default="")
    purchase_unit: Mapped[str] = mapped_column(String(50), default="个")
    use_unit: Mapped[str] = mapped_column(String(50), default="个")
    conversion_ratio: Mapped[Decimal] = mapped_column(QTY, default=Decimal("1"))
    stock_qty: Mapped[Decimal] = mapped_column(QTY, default=Decimal("0"))
    low_stock_qty: Mapped[Decimal] = mapped_column(QTY, default=Decimal("0"))
    avg_unit_price: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    default_supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Purchase(Base):
    __tablename__ = "purchases"
    id: Mapped[int] = mapped_column(primary_key=True)
    target_kind: Mapped[str] = mapped_column(String(20))  # material / part
    target_id: Mapped[int] = mapped_column()
    qty_rolls: Mapped[int | None] = mapped_column(nullable=True)
    grams_per_roll: Mapped[int | None] = mapped_column(nullable=True)
    qty: Mapped[Decimal | None] = mapped_column(QTY, nullable=True)
    goods_amount: Mapped[Decimal] = mapped_column(AMOUNT)
    shipping_fee: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchase_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Machine(Base):
    __tablename__ = "machines"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(AMOUNT)
    life_hours: Mapped[int] = mapped_column()
    power_w: Mapped[int] = mapped_column()
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CostSetting(Base):
    __tablename__ = "cost_settings"
    id: Mapped[int] = mapped_column(primary_key=True)  # 始终为 1
    electricity_price: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0.65"))
    default_machine_id: Mapped[int | None] = mapped_column(ForeignKey("machines.id"), nullable=True)
    scrap_rate: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0.05"))
    labor_rate: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("30"))
    default_markup: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("1.6"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class PrintItem(Base):
    __tablename__ = "print_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.id"))
    print_hours: Mapped[Decimal] = mapped_column(QTY)
    plates: Mapped[int] = mapped_column(default=1)
    nozzle: Mapped[str] = mapped_column(String(20), default="0.4mm")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    filaments: Mapped[list["PrintFilament"]] = relationship(
        back_populates="print_item", cascade="all, delete-orphan"
    )


class PrintFilament(Base):
    __tablename__ = "print_filaments"
    id: Mapped[int] = mapped_column(primary_key=True)
    print_item_id: Mapped[int] = mapped_column(ForeignKey("print_items.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    grams: Mapped[Decimal] = mapped_column(QTY)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    print_item: Mapped["PrintItem"] = relationship(back_populates="filaments")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mode: Mapped[str] = mapped_column(String(20), default="estimate")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    markup_rate: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("1.6"))
    total_cost: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    customer_price: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    bom_items: Mapped[list["BOMItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class BOMItem(Base):
    __tablename__ = "bom_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    kind: Mapped[str] = mapped_column(String(20))  # printitem/part/postprocess/subproduct
    ref_id: Mapped[int | None] = mapped_column(nullable=True)
    qty: Mapped[Decimal | None] = mapped_column(QTY, nullable=True)
    hours: Mapped[Decimal | None] = mapped_column(QTY, nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    subtotal: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    product: Mapped["Product"] = relationship(back_populates="bom_items")


class Quote(Base):
    __tablename__ = "quotes"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    mode: Mapped[str] = mapped_column(String(20), default="estimate")
    internal_cost: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    customer_price: Mapped[Decimal] = mapped_column(AMOUNT, default=Decimal("0"))
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
