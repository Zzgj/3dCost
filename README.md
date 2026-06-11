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

已完成阶段 1-3：后端骨架、仓储 CRUD（耗材/零件/供应商/机器/成本参数）、采购入库与加权平均到手价。
前端骨架已搭建，仓储管理页可联调。
