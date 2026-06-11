# 3D 打印成本控制平台 MVP 设计文档

> **项目**：3dcost - 拓竹 3D 打印机成本核算与报价平台  
> **版本**：v1.0.0  
> **日期**：2026-06-11  
> **范围**：阶段 1-6（核心链路）  
> **状态**：设计完成，待评审

---

## 一、设计目标

基于已有的《需求文档.md》，实现 MVP 核心链路：

**成功定义**：
1. 可通过 REST API 录入耗材、零件、采购批次，系统自动维护加权平均到手价和库存
2. 可通过 REST API 创建打印件，系统自动返回打印件成本（耗材成本 + 机时成本）
3. 可通过 REST API 创建产品 BOM，系统自动返回总成本明细树和建议报价
4. AI（Codex/Claude）可作为主要操作员，通过 API 完成 90% 的数据录入和查询
5. Web 前端可查看所有数据、手工录入/修正、扣减库存

**实施范围**：
- ✅ 阶段 1：骨架（FastAPI + SQLAlchemy + Vue3 + TypeScript）
- ✅ 阶段 2：仓储地基（耗材、零件、供应商、机器 CRUD）
- ✅ 阶段 3：采购与到手价（采购批次 → 自动更新加权平均价）
- ✅ 阶段 4：核算引擎（成本计算纯函数 + 单元测试）
- ✅ 阶段 5：打印件 API（录入 → 返回成本）
- ✅ 阶段 6：产品 API（创建 BOM → 返回成本明细树 + 扣减库存）
- ❌ 阶段 7-8：报价导出、统计看板（二期）

---

## 二、技术栈决策

### 后端

| 层 | 技术选型 | 版本 | 理由 |
|----|---------|------|------|
| 框架 | FastAPI | 最新稳定版 | 异步高性能、自动生成 OpenAPI 文档（AI 友好） |
| ORM | SQLAlchemy 2.0 | 2.0+ | 成熟稳定、复杂查询能力强、独立 schema 利于多视图 |
| Schema | Pydantic | v2 | 类型校验、API 文档生成 |
| 数据库 | SQLite → PostgreSQL | 3.x | 本地零配置，预留云端迁移路径 |
| 金额类型 | Decimal | - | 避免浮点误差，内部 4 位小数，展示 2 位 |
| 测试 | pytest + pytest-asyncio | - | 单元测试核心计算逻辑 |

### 前端

| 层 | 技术选型 | 版本 | 理由 |
|----|---------|------|------|
| 框架 | Vue 3 | 3.x | Composition API、TypeScript 支持好 |
| 语言 | TypeScript | 5.x | 类型安全、AI 协作友好 |
| 构建 | Vite | 最新 | 快速热更新 |
| UI 库 | Element Plus | 最新 | 后台管理组件最全、表格/表单成熟 |
| 路由 | Vue Router | 4.x | 官方路由 |
| HTTP | Axios | 最新 | 拦截器、请求封装 |

### 架构决策：经典三层分层

**选择原因**：
- 项目核心是"计算正确性"，不是"快速 CRUD"
- Services 层纯函数可单测（加权平均、成本计算）
- 最适合 AI 协作（每层职责单一，改一处不影响其他层）
- 符合需求文档的设计（services/costing.py、services/pricing.py）

```
Routers (HTTP 转换) → Services (业务计算) → Repositories (数据访问) → Database
```

---

## 三、系统架构

### 整体分层

```
┌─────────────────────────────────────────────────────────┐
│                    前端层 (Frontend)                      │
│          Vue 3 + TypeScript + Vite + Element Plus        │
│              HTTP 请求 → Backend REST API                 │
└─────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│                   API 层 (Routers)                       │
│     - 参数校验 (Pydantic schemas)                         │
│     - 响应包装 (统一格式)                                  │
│     - 错误处理 (HTTP 状态码)                               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  业务层 (Services)                        │
│     - 成本计算引擎 (costing.py)                           │
│     - 加权平均到手价 (pricing.py)                          │
│     - 库存扣减事务 (inventory.py)                          │
│     - BOM 循环检测 (bom_validator.py)                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                数据访问层 (Repositories)                   │
│     - CRUD 操作                                          │
│     - 复杂查询 (关联查询、聚合统计)                         │
│     - 事务管理                                            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   数据层 (Database)                       │
│              SQLite (后续可迁 PostgreSQL)                 │
└─────────────────────────────────────────────────────────┘
```

### 目录结构

```
3dcost/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI 应用入口、CORS、路由注册
│   │   ├── database.py            # SQLAlchemy 引擎、会话管理
│   │   ├── config.py              # 环境变量、配置加载
│   │   ├── models.py              # 所有 ORM 模型（单文件）
│   │   ├── schemas.py             # 所有 Pydantic schemas（单文件）
│   │   │
│   │   ├── routers/               # API 端点（薄层）
│   │   │   ├── __init__.py
│   │   │   ├── materials.py       # 耗材 CRUD
│   │   │   ├── parts.py           # 零件 CRUD
│   │   │   ├── purchases.py       # 采购批次录入
│   │   │   ├── suppliers.py       # 供应商管理
│   │   │   ├── machines.py        # 机器配置
│   │   │   ├── settings.py        # 成本参数配置
│   │   │   ├── print_items.py     # 打印件（返回成本）
│   │   │   ├── products.py        # 产品 BOM（返回成本明细树）
│   │   │   └── health.py          # 健康检查、元数据
│   │   │
│   │   ├── services/              # 业务逻辑（纯函数优先）
│   │   │   ├── __init__.py
│   │   │   ├── costing.py         # 成本计算引擎
│   │   │   ├── pricing.py         # 加权平均到手价计算
│   │   │   ├── inventory.py       # 库存更新、扣减事务
│   │   │   └── bom_validator.py   # BOM 循环引用检测
│   │   │
│   │   └── repositories/          # 数据访问（每实体一文件）
│   │       ├── __init__.py
│   │       ├── material_repo.py
│   │       ├── part_repo.py
│   │       ├── purchase_repo.py
│   │       ├── supplier_repo.py
│   │       ├── machine_repo.py
│   │       ├── settings_repo.py
│   │       ├── print_item_repo.py
│   │       └── product_repo.py
│   │
│   ├── tests/                     # pytest 单元测试
│   │   ├── test_pricing.py        # 加权平均到手价
│   │   ├── test_costing.py        # 成本计算
│   │   └── test_inventory.py     # 库存扣减事务
│   │
│   ├── data/                      # 数据目录（gitignore）
│   │   └── 3dcost.db              # SQLite 数据库
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/                   # API 调用封装
│   │   │   ├── client.ts          # Axios 配置
│   │   │   ├── materials.ts
│   │   │   ├── parts.ts
│   │   │   ├── purchases.ts
│   │   │   ├── suppliers.ts
│   │   │   ├── machines.ts
│   │   │   ├── settings.ts
│   │   │   ├── printItems.ts
│   │   │   └── products.ts
│   │   │
│   │   ├── types/                 # TypeScript 类型定义
│   │   │   ├── api.ts
│   │   │   ├── material.ts
│   │   │   ├── part.ts
│   │   │   ├── printItem.ts
│   │   │   └── product.ts
│   │   │
│   │   ├── components/            # 可复用组件
│   │   │   ├── BOMEditor.vue      # BOM 编辑器
│   │   │   ├── CostDetailTree.vue # 成本明细树
│   │   │   └── LowStockBadge.vue  # 低库存徽章
│   │   │
│   │   ├── views/                 # 页面组件
│   │   │   ├── Inventory.vue      # 仓储管理
│   │   │   ├── Purchases.vue      # 采购记录
│   │   │   ├── PrintItems.vue     # 打印件管理
│   │   │   ├── Products.vue       # 产品管理
│   │   │   └── Settings.vue       # 设置
│   │   │
│   │   ├── router/
│   │   │   └── index.ts
│   │   │
│   │   ├── utils/
│   │   │   └── format.ts          # 格式化工具
│   │   │
│   │   ├── App.vue
│   │   └── main.ts
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── .env.development
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-06-11-3dcost-mvp-design.md  # 本文档
│
└── README.md
```

**设计原则**：
- models.py 和 schemas.py 单文件：项目只有 10 张表，单文件更方便 AI 查找修改
- repositories 按实体拆分：每个 repo 只负责一个实体，职责单一
- services 按职能拆分：costing/pricing 是纯计算（可单测），inventory 协调多 repo

---

## 四、数据模型设计

### 数据库约定

- **金额**：内部 `Decimal(10, 4)`，API 展示四舍五入到 2 位
- **库存数量**：`Decimal(12, 3)`，允许小数（0.5 米、1.2 克）
- **重量**：统一克（g）
- **时间**：统一小时（h）
- **货币**：统一人民币元（¥）

### 核心数据表

#### 1. Material（耗材）

```python
class Material(Base):
    __tablename__ = "materials"
    
    id: int (PK)
    name: str                    # 拓竹PLA Basic 黑色
    type: str                    # PLA / PETG / ABS / TPU
    color: str                   # 黑色 / 白色 / 透明
    brand: str                   # 拓竹 / eSUN / Polymaker
    stock_g: Decimal             # 当前库存（克）
    low_stock_g: Decimal         # 低库存阈值（克）
    avg_price_per_g: Decimal     # 加权平均到手价（元/克）
    is_active: bool              # 是否启用
    created_at: datetime
    updated_at: datetime
```

#### 2. Part（零件）

```python
class Part(Base):
    __tablename__ = "parts"
    
    id: int (PK)
    name: str                    # 12V电源
    category: str                # 电源 / 电路板 / 轴承 / 螺丝 / 胶水
    spec: str                    # 规格说明
    purchase_unit: str           # 采购单位（盒 / 瓶 / 米）
    use_unit: str                # 使用单位（个 / 克 / 米）
    conversion_ratio: Decimal    # 换算比例（1盒=100个 → 100）
    stock_qty: Decimal           # 库存数量（使用单位）
    low_stock_qty: Decimal       # 低库存阈值
    avg_unit_price: Decimal      # 加权平均到手价（元/使用单位）
    default_supplier_id: int (FK → Supplier.id, nullable)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### 3. Supplier（供应商）

```python
class Supplier(Base):
    __tablename__ = "suppliers"
    
    id: int (PK)
    name: str                    # 淘宝-XX店铺
    note: str (nullable)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### 4. Purchase（采购批次）

```python
class Purchase(Base):
    __tablename__ = "purchases"
    
    id: int (PK)
    target_kind: str             # 'material' / 'part'
    target_id: int               # 关联到 Material.id 或 Part.id
    
    # 耗材专用字段
    qty_rolls: int (nullable)    # 卷数
    grams_per_roll: int (nullable)  # 克/卷规格
    
    # 零件专用字段
    qty: Decimal (nullable)      # 采购单位数量
    
    # 通用字段
    goods_amount: Decimal        # 货款（元）
    shipping_fee: Decimal        # 运费（元）
    supplier_id: int (FK → Supplier.id, nullable)
    purchase_url: str (nullable) # 采购链接
    purchased_at: datetime       # 采购日期
    created_at: datetime
```

**业务逻辑**：创建采购批次后，自动更新对应 Material 或 Part 的库存和加权平均到手价。

#### 5. Machine（机器）

```python
class Machine(Base):
    __tablename__ = "machines"
    
    id: int (PK)
    name: str                    # X1C / P1S
    price: Decimal               # 购机价（元）
    life_hours: int              # 预计寿命（小时）
    power_w: int                 # 功率（瓦）
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### 6. CostSetting（成本参数，单例表）

```python
class CostSetting(Base):
    __tablename__ = "cost_settings"
    
    id: int (PK, 始终为1)
    electricity_price: Decimal   # 电费单价（元/kWh）
    default_machine_id: int (FK → Machine.id)
    scrap_rate: Decimal          # 废品率（0.05 = 5%）
    labor_rate: Decimal          # 人工工时单价（元/小时）
    default_markup: Decimal      # 默认加成倍率（1.6 = 160%）
    updated_at: datetime
```

#### 7. PrintItem（打印件）

```python
class PrintItem(Base):
    __tablename__ = "print_items"
    
    id: int (PK)
    name: str                    # 小型排风机
    machine_id: int (FK → Machine.id)
    print_hours: Decimal         # 打印耗时（小时）
    plates: int                  # 盘数
    nozzle: str                  # 喷嘴规格（0.4mm）
    source_url: str (nullable)   # MakerWorld 链接
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

#### 8. PrintFilament（打印件耗材用量，多色支持）

```python
class PrintFilament(Base):
    __tablename__ = "print_filaments"
    
    id: int (PK)
    print_item_id: int (FK → PrintItem.id)
    material_id: int (FK → Material.id)
    grams: Decimal               # 该耗材用量（克）
    created_at: datetime
```

**业务逻辑**：一个 PrintItem 可以有多个 PrintFilament（多色打印）。

#### 9. Product（产品）

```python
class Product(Base):
    __tablename__ = "products"
    
    id: int (PK)
    name: str                    # 排风扇成品
    note: str (nullable)
    mode: str                    # 'estimate' / 'actual'
    status: str                  # 'draft' / 'completed'
    markup_rate: Decimal         # 加成倍率
    total_cost: Decimal          # 总成本（自动计算）
    customer_price: Decimal      # 客户报价（自动计算）
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**状态说明**：
- `draft`：草稿，可随意修改 BOM
- `completed`：已完成，BOM 锁定

#### 10. BOMItem（物料清单）

```python
class BOMItem(Base):
    __tablename__ = "bom_items"
    
    id: int (PK)
    product_id: int (FK → Product.id)
    kind: str                    # 'printitem' / 'part' / 'postprocess' / 'subproduct'
    ref_id: int (nullable)       # 关联ID
    qty: Decimal (nullable)      # 数量（零件/子产品时）
    hours: Decimal (nullable)    # 工时（后处理时）
    unit_price: Decimal          # 单价快照
    subtotal: Decimal            # 小计
    created_at: datetime
```

### 数据关系图

```
Supplier ─────┐
              ↓
Purchase ────→ Material / Part
              (更新库存 + 到手价)
                ↓                    ↓
           PrintFilament ←─── PrintItem
                                    ↓
Machine ──────────────────────→ PrintItem
                                    ↓
CostSetting ─────────────────→ Product ←── BOMItem ──→ PrintItem / Part / Product(子产品)
```

### 索引策略

```sql
CREATE INDEX idx_purchase_target ON purchases(target_kind, target_id);
CREATE INDEX idx_print_filament ON print_filaments(print_item_id);
CREATE INDEX idx_bom_product ON bom_items(product_id);
CREATE INDEX idx_bom_ref ON bom_items(kind, ref_id);
CREATE INDEX idx_material_stock ON materials(stock_g, low_stock_g) WHERE is_active = true;
CREATE INDEX idx_part_stock ON parts(stock_qty, low_stock_qty) WHERE is_active = true;
```

---

## 五、核心业务逻辑设计

### 1. 加权平均到手价计算（services/pricing.py）

**算法**：

```python
def calculate_weighted_avg_price(purchases: List[Purchase]) -> Decimal:
    """
    公式：(所有批次的货款+运费总和) / (所有批次的总数量)
    
    示例：
    - 第1批：1个，货款16 + 运费4 = 20 → 单价 20/个
    - 第2批：2个，货款28 + 运费4 = 32
    - 加权平均 = (20 + 32) / (1 + 2) = 17.33/个
    """
    total_amount = sum(p.goods_amount + p.shipping_fee for p in purchases)
    
    if purchases[0].target_kind == 'material':
        total_qty = sum(p.qty_rolls * p.grams_per_roll for p in purchases)
    else:  # part
        total_qty = sum(p.qty * p.conversion_ratio for p in purchases)
    
    return total_amount / total_qty if total_qty > 0 else Decimal('0')
```

**触发时机**：创建新采购批次后立即重算。

### 2. 打印件成本计算（services/costing.py）

**输入**：
- PrintItem（打印时间）
- PrintFilaments（每种耗材的克重）
- Machine（折旧、功率）
- CostSetting（电价）

**输出**：
```python
{
    "material_cost": Decimal("8.54"),
    "machine_cost": Decimal("6.24"),
    "total": Decimal("14.78")
}
```

**算法**：

```python
def calculate_print_item_cost(
    print_item: PrintItem,
    filaments: List[PrintFilament],
    materials: Dict[int, Material],
    machine: Machine,
    electricity_price: Decimal
) -> Dict[str, Decimal]:
    # 1. 耗材成本（多色求和）
    material_cost = sum(
        f.grams * materials[f.material_id].avg_price_per_g
        for f in filaments
    )
    
    # 2. 机时成本
    depreciation_per_h = machine.price / machine.life_hours
    electricity_per_h = (machine.power_w / Decimal('1000')) * electricity_price
    machine_cost = print_item.print_hours * (depreciation_per_h + electricity_per_h)
    
    return {
        "material_cost": round_decimal(material_cost, 2),
        "machine_cost": round_decimal(machine_cost, 2),
        "total": round_decimal(material_cost + machine_cost, 2)
    }
```

### 3. 产品总成本计算（services/costing.py）

**输入**：
- Product（加成倍率）
- BOMItems（打印件、零件、后处理、子产品）
- CostSetting（废品率、人工单价）

**输出**：
```python
{
    "printitems_cost": Decimal("14.78"),
    "parts_cost": Decimal("24.13"),
    "postprocess_cost": Decimal("24.00"),
    "subproduct_cost": Decimal("0.00"),
    "subtotal": Decimal("62.91"),
    "scrap_cost": Decimal("3.15"),
    "total_cost": Decimal("66.06"),
    "customer_price": Decimal("105.70")
}
```

**算法（含子产品递归）**：

```python
def calculate_product_cost(
    product: Product,
    bom_items: List[BOMItem],
    print_items: Dict[int, PrintItem],
    parts: Dict[int, Part],
    labor_rate: Decimal,
    scrap_rate: Decimal,
    visited: Set[int] = None
) -> Dict[str, Decimal]:
    if visited is None:
        visited = set()
    
    # 循环引用检测
    if product.id in visited:
        raise ValueError(f"BOM循环引用: Product {product.id}")
    visited.add(product.id)
    
    printitems_cost = Decimal('0')
    parts_cost = Decimal('0')
    postprocess_cost = Decimal('0')
    subproduct_cost = Decimal('0')
    
    for item in bom_items:
        if item.kind == 'printitem':
            printitems_cost += item.unit_price * item.qty
        elif item.kind == 'part':
            parts_cost += parts[item.ref_id].avg_unit_price * item.qty
        elif item.kind == 'postprocess':
            postprocess_cost += item.hours * labor_rate
        elif item.kind == 'subproduct':
            sub_product = Product.get(item.ref_id)
            sub_cost = calculate_product_cost(
                sub_product, sub_product.bom_items,
                print_items, parts, labor_rate, scrap_rate, visited
            )
            subproduct_cost += sub_cost['total_cost'] * item.qty
    
    subtotal = printitems_cost + parts_cost + postprocess_cost + subproduct_cost
    scrap_cost = subtotal * scrap_rate
    total_cost = subtotal + scrap_cost
    customer_price = total_cost * product.markup_rate
    
    return {
        "printitems_cost": round_decimal(printitems_cost, 2),
        "parts_cost": round_decimal(parts_cost, 2),
        "postprocess_cost": round_decimal(postprocess_cost, 2),
        "subproduct_cost": round_decimal(subproduct_cost, 2),
        "subtotal": round_decimal(subtotal, 2),
        "scrap_cost": round_decimal(scrap_cost, 2),
        "total_cost": round_decimal(total_cost, 2),
        "customer_price": round_decimal(customer_price, 2)
    }
```

### 4. 库存扣减事务（services/inventory.py）

**业务规则**：
- 同一事务内完成所有扣减
- 任一项库存不足，整体回滚
- 扣减前检查，扣减后记录

**算法**：

```python
def consume_stock_for_product(
    product: Product,
    bom_items: List[BOMItem],
    db: Session
) -> Dict[str, Any]:
    consumed = {"materials": [], "parts": []}
    warnings = []
    
    # 1. 先检查所有库存是否充足
    for item in bom_items:
        if item.kind == 'printitem':
            print_item = db.query(PrintItem).get(item.ref_id)
            for filament in print_item.filaments:
                material = db.query(Material).get(filament.material_id)
                required = filament.grams * item.qty
                if material.stock_g < required:
                    raise ValueError(
                        f"耗材库存不足: {material.name}，需要 {required}g，库存 {material.stock_g}g"
                    )
        elif item.kind == 'part':
            part = db.query(Part).get(item.ref_id)
            if part.stock_qty < item.qty:
                raise ValueError(
                    f"零件库存不足: {part.name}，需要 {item.qty}，库存 {part.stock_qty}"
                )
    
    # 2. 检查通过，开始扣减
    for item in bom_items:
        if item.kind == 'printitem':
            print_item = db.query(PrintItem).get(item.ref_id)
            for filament in print_item.filaments:
                material = db.query(Material).get(filament.material_id)
                deduct = filament.grams * item.qty
                material.stock_g -= deduct
                consumed["materials"].append({
                    "name": material.name,
                    "deducted_g": float(deduct),
                    "remaining_g": float(material.stock_g)
                })
                if material.stock_g < material.low_stock_g:
                    warnings.append(f"{material.name} 低于库存阈值")
        
        elif item.kind == 'part':
            part = db.query(Part).get(item.ref_id)
            part.stock_qty -= item.qty
            consumed["parts"].append({
                "name": part.name,
                "deducted_qty": float(item.qty),
                "remaining_qty": float(part.stock_qty)
            })
            if part.stock_qty < part.low_stock_qty:
                warnings.append(f"{part.name} 低于库存阈值")
    
    db.commit()
    return {"consumed": consumed, "warnings": warnings}
```

### 5. BOM 循环引用检测（services/bom_validator.py）

```python
def check_bom_cycle(product_id: int, bom_items: List[BOMItem], db: Session):
    def dfs(pid: int, visited: Set[int], path: List[int]):
        if pid in visited:
            raise ValueError(f"BOM循环引用: {' → '.join(map(str, path + [pid]))}")
        
        visited.add(pid)
        path.append(pid)
        
        sub_items = [item for item in bom_items if item.kind == 'subproduct']
        for item in sub_items:
            dfs(item.ref_id, visited.copy(), path.copy())
    
    dfs(product_id, set(), [])
```

---

## 六、API 设计

### 通用响应格式

**成功（单条）**：
```json
{
  "data": { /* 实体对象 */ },
  "meta": {
    "request_id": "uuid",
    "warnings": []
  }
}
```

**成功（列表）**：
```json
{
  "data": [ /* 实体数组 */ ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 128
  },
  "meta": {
    "request_id": "uuid",
    "warnings": []
  }
}
```

**错误**：
```json
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "耗材库存不足",
    "details": {
      "material_id": 3,
      "required_g": 200,
      "stock_g": 120
    }
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

**错误码**：
- `VALIDATION_ERROR`：请求参数错误
- `NOT_FOUND`：资源不存在
- `LOCKED_RESOURCE`：资源已锁定
- `INSUFFICIENT_STOCK`：库存不足
- `COST_SOURCE_MISSING`：缺少价格来源
- `BOM_CYCLE_DETECTED`：BOM 循环引用

### 核心 API 端点

#### 1. 耗材管理
```
GET    /api/materials
POST   /api/materials
GET    /api/materials/:id
PATCH  /api/materials/:id
DELETE /api/materials/:id
```

#### 2. 零件管理
```
GET    /api/parts?search={kw}&category={cat}
POST   /api/parts
GET    /api/parts/:id
PATCH  /api/parts/:id
DELETE /api/parts/:id
```

#### 3. 采购批次
```
POST   /api/purchases        # 录入 → 自动更新库存和到手价
GET    /api/purchases?target_kind={material|part}&target_id={id}
```

**耗材采购请求**：
```json
{
  "target_kind": "material",
  "target_id": 3,
  "qty_rolls": 2,
  "grams_per_roll": 1000,
  "goods_amount": 160,
  "shipping_fee": 10,
  "supplier_id": 1,
  "purchase_url": "https://...",
  "purchased_at": "2026-06-10"
}
```

**响应**：
```json
{
  "data": {
    "purchase": { /* 采购批次对象 */ },
    "updated_avg_price": 0.085,
    "total_stock": 5200
  }
}
```

#### 4. 供应商管理
```
GET    /api/suppliers
POST   /api/suppliers
GET    /api/suppliers/:id
PATCH  /api/suppliers/:id
```

#### 5. 机器管理
```
GET    /api/machines
POST   /api/machines
GET    /api/machines/:id
PATCH  /api/machines/:id
```

#### 6. 成本参数配置
```
GET    /api/settings/cost
PATCH  /api/settings/cost
```

#### 7. 打印件管理（返回成本）
```
POST   /api/print-items      # 创建 → 自动返回成本
GET    /api/print-items
GET    /api/print-items/:id
PATCH  /api/print-items/:id  # 更新 → 返回新成本
DELETE /api/print-items/:id
```

**创建请求（AI 调用）**：
```json
{
  "name": "小型排风机",
  "machine_id": 1,
  "print_hours": 9.6,
  "plates": 4,
  "nozzle": "0.4mm",
  "source_url": "https://makerworld.com.cn/zh/models/2275796",
  "filaments": [
    {"material_id": 3, "grams": 200},
    {"material_id": 5, "grams": 58}
  ]
}
```

**响应（自动计算成本）**：
```json
{
  "data": {
    "id": 12,
    "name": "小型排风机",
    "filaments": [
      {"material_id": 3, "material_name": "拓竹PLA黑色", "grams": 200}
    ],
    "cost": {
      "material_cost": 8.54,
      "machine_cost": 6.24,
      "total": 14.78
    }
  }
}
```

#### 8. 产品管理（返回成本明细树）
```
POST   /api/products                        # 创建 → 返回成本明细树
GET    /api/products?status={draft|completed}&mode={estimate|actual}
GET    /api/products/:id
PATCH  /api/products/:id
DELETE /api/products/:id
POST   /api/products/:id/consume-stock      # 手动扣减库存
POST   /api/products/:id/complete           # 标记已完成
```

**创建请求（AI 调用）**：
```json
{
  "name": "排风扇成品",
  "mode": "estimate",
  "markup_rate": 1.6,
  "bom_items": [
    {"kind": "printitem", "ref_id": 12, "qty": 1},
    {"kind": "part", "ref_id": 8, "qty": 1},
    {"kind": "part", "ref_id": 9, "qty": 1},
    {"kind": "postprocess", "hours": 0.8}
  ]
}
```

**响应（自动计算成本明细树）**：
```json
{
  "data": {
    "id": 45,
    "name": "排风扇成品",
    "bom_items": [
      {
        "kind": "printitem",
        "ref_name": "小型排风机",
        "qty": 1,
        "unit_price": 14.78,
        "subtotal": 14.78
      }
    ],
    "cost_detail": {
      "printitems_cost": 14.78,
      "parts_cost": 24.13,
      "postprocess_cost": 24.00,
      "subtotal": 62.91,
      "scrap_cost": 3.15,
      "total_cost": 66.06,
      "customer_price": 105.70
    }
  }
}
```

#### 9. 系统接口
```
GET    /api/health
GET    /api/meta    # 枚举值、版本信息（供 AI 查询）
```

---

## 七、前端设计

### 页面结构（5 个核心页面）

1. **仓储管理页（Inventory.vue）**
   - Tab 1: 耗材列表
   - Tab 2: 零件列表
   - 低库存高亮

2. **采购记录页（Purchases.vue）**
   - 采购表单（区分耗材/零件）
   - 采购历史列表

3. **打印件管理页（PrintItems.vue）**
   - 打印件列表（显示成本）
   - 创建/编辑表单（支持多耗材）

4. **产品管理页（Products.vue）**
   - 产品列表
   - BOM 编辑器
   - 成本明细树展示
   - 操作：扣减库存、标记完成

5. **设置页（Settings.vue）**
   - Tab 1: 成本参数
   - Tab 2: 机器管理
   - Tab 3: 供应商管理

### 核心组件

#### BOMEditor.vue（BOM 编辑器）
- 添加打印件/零件/后处理
- 显示单价和小计
- 支持删除、排序

#### CostDetailTree.vue（成本明细树）
- 树形展示成本结构
- 可折叠/展开
- 高亮总成本和客户报价

---

## 八、实施计划

### 阶段 1：骨架（1-2 天）
- [ ] FastAPI 项目初始化 + SQLAlchemy + SQLite
- [ ] 数据模型定义（所有表）+ Alembic 迁移
- [ ] CORS 配置 + 统一响应格式
- [ ] Vue3 + TypeScript + Vite + Element Plus 初始化
- [ ] 前后端联调测试

### 阶段 2：仓储地基（2-3 天）
- [ ] 耗材 CRUD API + Repository
- [ ] 零件 CRUD API + Repository
- [ ] 供应商 CRUD API
- [ ] 机器 CRUD API
- [ ] 成本参数配置 API
- [ ] Web 对应页面（表格 + 表单）

### 阶段 3：采购与到手价（2-3 天）
- [ ] `services/pricing.py` 加权平均到手价计算
- [ ] 采购批次 API（耗材/零件分别处理）
- [ ] 自动更新库存 + 到手价逻辑
- [ ] 单元测试（电源例子：20、32 → 17.33）
- [ ] Web 采购记录页

### 阶段 4：核算引擎（2-3 天）
- [ ] `services/costing.py` 打印件成本计算
- [ ] `services/costing.py` 产品成本计算（含递归）
- [ ] 单元测试（多色、多层 BOM、废品率）

### 阶段 5：打印件 API（1-2 天）
- [ ] 打印件 CRUD API，POST 时返回 cost
- [ ] Web 打印件列表/详情/编辑页

### 阶段 6：产品 API（3-4 天）
- [ ] 产品 CRUD API + BOMItem 关联逻辑
- [ ] POST 时返回 cost_detail 树
- [ ] 状态管理（draft/completed）
- [ ] Web 产品列表/详情/BOM 编辑页
- [ ] 扣减库存 API + 按钮

**总计：约 11-17 天**

---

## 九、验收标准

### 核心链路
1. ✅ AI 录入打印件 → 系统返回成本
2. ✅ AI 创建产品 → 系统返回成本明细和建议报价
3. ✅ Web 可查看所有数据、手工修改
4. ✅ 可手动扣减库存

### 功能清单
- [ ] 耗材采购批次自动转换克数并更新到手价
- [ ] 零件采购批次自动转换使用单位并更新到手价
- [ ] 打印件 API 返回含多色耗材成本
- [ ] 产品 API 返回含完整成本明细树
- [ ] 多层 BOM 递归计算正确
- [ ] 子产品循环引用会被拒绝
- [ ] 产品完成锁定后不可直接修改 BOM
- [ ] 库存手动扣减正常
- [ ] 库存不足时扣减整体失败
- [ ] 低库存预警正常触发

### 单元测试
- [ ] `pytest backend/tests/test_pricing.py`：加权平均到手价（电源例子 → 17.33）
- [ ] `pytest backend/tests/test_costing.py`：多色打印件成本、多层 BOM、废品率

### AI 协作验收
- [ ] AI 可通过 `GET /api/meta` 获取枚举值
- [ ] AI 可通过 REST API 完成"录入打印件 → 创建产品 → 返回建议报价"主流程
- [ ] AI 对错误能拿到明确错误码和可解释信息

---

## 十、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| MakerWorld 页面结构变化 | AI 不能稳定抓取 | 平台不依赖抓取器，允许手动录入 |
| 采购价格被历史批次改动影响 | 历史报价不可信 | BOM 单价保存快照 |
| SQLite 文件损坏 | 数据丢失 | 固定数据目录 + 手动备份 |
| 多层 BOM 递归复杂 | 成本算错或死循环 | 单元测试 + 循环引用检测 |
| 金额浮点误差 | 报价尾差 | 使用 Decimal，展示层统一四舍五入 |

---

## 十一、后续扩展（二期）

- 报价单导出（图片/PDF）
- 统计看板（月度成本/利润、耗材消耗）
- 数据备份与恢复
- 采购优化（买几个最划算）
- 自动库存扣减
- 微信小程序上架

---

**文档版本**：v1.0.0  
**状态**：设计完成，待评审

