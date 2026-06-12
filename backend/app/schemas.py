from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Material ----------
class MaterialCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)
    color: str = ""
    brand: str = ""
    low_stock_g: Decimal = Decimal("0")


class MaterialUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    type: str | None = Field(default=None, max_length=50)
    color: str | None = None
    brand: str | None = None
    low_stock_g: Decimal | None = None
    is_active: bool | None = None


class MaterialOut(ORMModel):
    id: int
    name: str
    type: str
    color: str
    brand: str
    stock_g: Decimal
    low_stock_g: Decimal
    avg_price_per_g: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- Part ----------
class PartCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = ""
    spec: str = ""
    purchase_unit: str = "个"
    use_unit: str = "个"
    conversion_ratio: Decimal = Decimal("1")
    low_stock_qty: Decimal = Decimal("0")
    default_supplier_id: int | None = None


class PartUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    category: str | None = None
    spec: str | None = None
    purchase_unit: str | None = None
    use_unit: str | None = None
    conversion_ratio: Decimal | None = None
    low_stock_qty: Decimal | None = None
    default_supplier_id: int | None = None
    is_active: bool | None = None


class PartOut(ORMModel):
    id: int
    name: str
    category: str
    spec: str
    purchase_unit: str
    use_unit: str
    conversion_ratio: Decimal
    stock_qty: Decimal
    low_stock_qty: Decimal
    avg_unit_price: Decimal
    default_supplier_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- Supplier ----------
class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = None


class SupplierUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    note: str | None = None
    is_active: bool | None = None


class SupplierOut(ORMModel):
    id: int
    name: str
    note: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- Machine ----------
class MachineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(ge=0)
    life_hours: int = Field(gt=0)
    power_w: int = Field(ge=0)


class MachineUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    price: Decimal | None = None
    life_hours: int | None = Field(default=None, gt=0)
    power_w: int | None = None
    is_active: bool | None = None


class MachineOut(ORMModel):
    id: int
    name: str
    price: Decimal
    life_hours: int
    power_w: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- CostSetting ----------
class CostSettingUpdate(BaseModel):
    electricity_price: Decimal | None = Field(default=None, ge=0)
    default_machine_id: int | None = None
    scrap_rate: Decimal | None = Field(default=None, ge=0)
    labor_rate: Decimal | None = Field(default=None, ge=0)
    default_markup: Decimal | None = Field(default=None, ge=0)


class CostSettingOut(ORMModel):
    id: int
    electricity_price: Decimal
    default_machine_id: int | None
    scrap_rate: Decimal
    labor_rate: Decimal
    default_markup: Decimal
    updated_at: datetime


# ---------- Purchase ----------
class PurchaseCreate(BaseModel):
    target_kind: str = Field(pattern="^(material|part)$")
    target_id: int
    # 耗材专用
    qty_rolls: int | None = Field(default=None, ge=1)
    grams_per_roll: int | None = Field(default=None, ge=1)
    # 零件专用
    qty: Decimal | None = Field(default=None, gt=0)
    # 通用
    goods_amount: Decimal = Field(ge=0)
    shipping_fee: Decimal = Field(default=Decimal("0"), ge=0)
    supplier_id: int | None = None
    purchase_url: str | None = Field(default=None, max_length=500)
    purchased_at: datetime | None = None


class PurchaseOut(ORMModel):
    id: int
    target_kind: str
    target_id: int
    qty_rolls: int | None
    grams_per_roll: int | None
    qty: Decimal | None
    goods_amount: Decimal
    shipping_fee: Decimal
    supplier_id: int | None
    purchase_url: str | None
    purchased_at: datetime
    created_at: datetime


class PurchaseResult(BaseModel):
    purchase: PurchaseOut
    updated_avg_price: Decimal
    total_stock: Decimal


# ---------- PrintItem ----------
class PrintFilamentIn(BaseModel):
    material_id: int
    grams: Decimal = Field(gt=0)


class PrintFilamentOut(ORMModel):
    material_id: int
    grams: Decimal


class CostOut(BaseModel):
    material_cost: Decimal
    machine_cost: Decimal
    total: Decimal


class PrintItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    machine_id: int
    print_hours: Decimal = Field(ge=0)
    plates: int = Field(default=1, ge=1)
    nozzle: str = "0.4mm"
    source_url: str | None = Field(default=None, max_length=500)
    filaments: list[PrintFilamentIn] = []


class PrintItemUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    machine_id: int | None = None
    print_hours: Decimal | None = Field(default=None, ge=0)
    plates: int | None = Field(default=None, ge=1)
    nozzle: str | None = None
    source_url: str | None = Field(default=None, max_length=500)
    filaments: list[PrintFilamentIn] | None = None


class PrintItemOut(ORMModel):
    id: int
    name: str
    machine_id: int
    print_hours: Decimal
    plates: int
    nozzle: str
    source_url: str | None
    filaments: list[PrintFilamentOut]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------- Product / BOM ----------
class BOMItemIn(BaseModel):
    kind: str = Field(pattern="^(printitem|part|postprocess|subproduct)$")
    ref_id: int | None = None
    qty: Decimal | None = Field(default=None, gt=0)
    hours: Decimal | None = Field(default=None, ge=0)


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=500)
    mode: str = Field(default="estimate", pattern="^(estimate|actual)$")
    markup_rate: Decimal = Field(default=Decimal("1.6"), gt=0)
    bom_items: list[BOMItemIn] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=500)
    mode: str | None = Field(default=None, pattern="^(estimate|actual)$")
    markup_rate: Decimal | None = Field(default=None, gt=0)
    bom_items: list[BOMItemIn] | None = None


class BOMItemOut(ORMModel):
    id: int
    kind: str
    ref_id: int | None
    ref_name: str | None = None
    qty: Decimal | None
    hours: Decimal | None
    unit_price: Decimal
    subtotal: Decimal


class CostDetail(BaseModel):
    printitems_cost: Decimal
    parts_cost: Decimal
    postprocess_cost: Decimal
    subproduct_cost: Decimal
    subtotal: Decimal
    scrap_cost: Decimal
    total_cost: Decimal
    customer_price: Decimal


class ProductOut(ORMModel):
    id: int
    name: str
    note: str | None
    mode: str
    status: str
    markup_rate: Decimal
    total_cost: Decimal
    customer_price: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductDetailOut(ProductOut):
    bom_items: list[BOMItemOut]
    cost_detail: CostDetail
