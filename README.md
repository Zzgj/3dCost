# 3dcost 成本控制平台

3D 打印成本核算与报价平台。后端 FastAPI，前端 Vue3 + Element Plus。

## 后端启动

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档：http://127.0.0.1:8000/docs

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问：http://127.0.0.1:5173

## 测试

```bash
cd backend && . .venv/bin/activate && pytest -q
```

## 当前进度

已完成 MVP 主链路：仓储 CRUD、采购入库与加权平均到手价、打印件成本核算、产品 BOM 成本明细、手动库存扣减、完成锁定、报价快照/HTML 导出、低库存/月度/耗材消耗统计、手动备份入口。

前端已提供仓储、采购、打印件、产品报价、报价历史、统计看板、数据备份和设置页面。
