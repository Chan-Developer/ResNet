# ResNet API + Vue 前端

本目录已提供：

- `backend/app.py`：FastAPI 推理服务
- `frontend/index.html`：Vue3 前端页面（上传图片调用 `/predict`）

## 1) 启动后端 API

在 `ResNet` 目录执行：

```bash
cd /data/clj/Project/ProgrammingStudy/ResNet
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

默认会加载：

- 模型：`resnet50_阶段二_(全局微调)_best.pth`
- 类别目录：`datasets/color`

也可以通过环境变量覆盖：

```bash
MODEL_PATH="/your/model.pth" DATASET_DIR="/your/dataset_dir" uvicorn backend.app:app --reload
```

## 2) 打开前端页面

建议用一个静态服务器打开（避免本地文件跨域限制）：

```bash
cd /data/clj/Project/ProgrammingStudy/ResNet/frontend
python -m http.server 5173
```

然后浏览器访问：

- `http://127.0.0.1:5173`

## 3) 接口说明

- `GET /health`：查看服务状态
- `GET /classes`：返回类别列表
- `POST /predict?top_k=5`：上传图片预测
  - 表单字段：`file`（图片文件）
