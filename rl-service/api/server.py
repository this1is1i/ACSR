# api/server.py
# FastAPI REST API 服务 —— 暴露推荐系统核心能力

from __future__ import annotations
import sys
import os
import asyncio
import logging
from typing import List, Optional
from contextlib import asynccontextmanager

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    raise ImportError("请安装依赖：pip install fastapi uvicorn pydantic")

from config import default_config
from services.recommendation_service import RecommendationService
from train import train

logger = logging.getLogger(__name__)

# ── 全局服务实例（懒加载）────────────────────────────────────────
_service: Optional[RecommendationService] = None
_training_status = {"is_training": False, "last_episode": 0, "best_reward": -999.0}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化服务。"""
    global _service
    logger.info("正在初始化推荐服务...")
    _service = RecommendationService(default_config)
    logger.info("推荐服务初始化完成，API 就绪")
    yield
    logger.info("服务关闭")


app = FastAPI(
    title="科研推荐系统 REST API",
    description=(
        "基于 Actor-Critic 强化学习的科研内容推荐服务。\n\n"
        "支持 Top-K 推荐、推荐解释生成，可与 Spring Boot 后端对接。"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS 配置（允许 Spring Boot 跨域调用）────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 生产环境替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic 请求 / 响应模型 ──────────────────────────────────────

class RecommendRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "user_001"}, description="用户唯一标识")
    k: int = Field(default=10, ge=1, le=50, description="推荐数量")
    history: Optional[List[str]] = Field(
        default=None, description="已读论文 ID 列表（可选，用于过滤）"
    )
    strategy: str = Field(
        default="hybrid",
        description="召回策略: similarity | popular | hybrid"
    )


class RecommendationItemResponse(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    year: int
    score: float
    rank: int
    reason: str
    reason_details: List[str]
    similarity_score: float
    topics: List[str]
    citation_count: int
    confidence: float


class RecommendResponse(BaseModel):
    user_id: str
    k: int
    model_version: str
    latency_ms: float
    recommendations: List[RecommendationItemResponse]


class TrainRequest(BaseModel):
    episodes: Optional[int] = Field(
        default=None, description="训练轮次（None 使用配置文件默认值）"
    )


class TrainResponse(BaseModel):
    message: str
    status: str


class ModelInfoResponse(BaseModel):
    model_version: str
    train_step: int
    episode_count: int
    model_path: str
    state_dim: int
    base_state_dim: int
    action_num: int
    top_k: int
    use_kg: bool
    kg_embedding_dim: int
    device: str
    is_training: bool
    last_episode: int
    best_reward: float


class LearningPathRequest(BaseModel):
    user_id: str = Field(..., description="用户 ID")
    target_topic: str = Field(..., description="目标研究方向关键词")
    history: Optional[List[str]] = Field(default=None, description="用户已读论文 ID 列表")
    max_nodes: int = Field(default=20, ge=5, le=50, description="路径最大节点数")


class LearningPathNodeResponse(BaseModel):
    node_id: str
    label: str
    node_type: str
    mastery: float
    depth: int
    year: Optional[int] = None
    color: str = "#3B82F6"
    glow_intensity: float = 0.0


class LearningPathResponse(BaseModel):
    user_id: str
    topic: str
    estimated_hours: float
    coverage: float
    nodes: List[LearningPathNodeResponse]
    edges: List[dict]


# ── API 路由 ──────────────────────────────────────────────────────

@app.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="获取 Top-K 科研推荐",
    tags=["推荐"],
)
async def recommend(request: RecommendRequest):
    """
    为指定用户生成 Top-K 科研内容推荐。

    **Spring Boot 对接示例（Java）**：
    ```java
    RestTemplate rt = new RestTemplate();
    String url = "http://localhost:8000/recommend";
    RecommendRequest req = new RecommendRequest("user_001", 10);
    RecommendResponse resp = rt.postForObject(url, req, RecommendResponse.class);
    ```
    """
    if _service is None:
        raise HTTPException(status_code=503, detail="推荐服务尚未初始化")
    try:
        response = _service.get_recommendations(
            user_id=request.user_id,
            k=request.k,
            history=request.history,
            strategy=request.strategy,
        )
        result_dict = _service.to_dict(response)
        return result_dict
    except Exception as e:
        logger.exception(f"推荐失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐服务异常: {str(e)}")


@app.post(
    "/train",
    response_model=TrainResponse,
    summary="触发模型训练",
    tags=["训练"],
)
async def trigger_train(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
):
    """
    异步触发 Actor-Critic 模型训练。
    训练在后台线程执行，不阻塞 API 响应。
    训练完成后可调用 /model/reload 热重载新权重。
    """
    if _training_status["is_training"]:
        raise HTTPException(
            status_code=409,
            detail="模型正在训练中，请等待当前训练完成"
        )

    def _run_train():
        global _service
        _training_status["is_training"] = True
        try:
            import copy
            config = copy.copy(default_config)
            if request.episodes:
                config.max_episodes = request.episodes
            _, metrics = train(config)
            if _service:
                _service.reload_model()
            _training_status["last_episode"] = metrics["total_episodes"]
            _training_status["best_reward"] = metrics["best_reward"]
            logger.info(
                f"后台训练完成，best_reward={metrics['best_reward']:.4f}, "
                f"模型已热重载"
            )
        except Exception as e:
            logger.exception(f"训练失败: {e}")
        finally:
            _training_status["is_training"] = False

    background_tasks.add_task(_run_train)
    return TrainResponse(
        message="训练已在后台启动，可通过 GET /model/info 查看训练状态",
        status="started",
    )


@app.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="查询模型状态",
    tags=["模型管理"],
)
async def model_info():
    """返回当前模型训练状态、版本信息和超参数。"""
    if _service is None:
        raise HTTPException(status_code=503, detail="推荐服务尚未初始化")
    info = _service.get_model_info()
    info.update({
        "is_training":  _training_status["is_training"],
        "last_episode": _training_status["last_episode"],
        "best_reward":  _training_status["best_reward"],
    })
    return info


@app.post(
    "/model/reload",
    summary="热重载模型权重",
    tags=["模型管理"],
)
async def reload_model():
    """无需重启服务，直接重载最新模型权重。"""
    if _service is None:
        raise HTTPException(status_code=503, detail="推荐服务尚未初始化")
    try:
        _service.reload_model()
        return {"message": "模型热重载成功", "model_version": _service.MODEL_VERSION}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型重载失败: {str(e)}")


@app.get("/health", summary="健康检查", tags=["系统"])
async def health_check():
    """服务健康检查接口（供 Spring Boot / K8s 使用）。"""
    return {
        "status": "healthy",
        "service": "rl-recommender",
        "version": "1.0.0",
        "model_ready": _service is not None,
    }


@app.post(
    "/learning-path",
    response_model=LearningPathResponse,
    summary="生成学习路径",
    tags=["知识图谱"],
)
async def generate_learning_path(request: LearningPathRequest):
    """
    基于知识图谱为用户生成从当前知识状态到目标主题的学习路径。
    返回掌握度、颜色映射和发光强度，供前端 Three.js 三维可视化使用。

    颜色方案：蓝(0.0) → 橙(0.5) → 绿(1.0)
    """
    if _service is None:
        raise HTTPException(status_code=503, detail="推荐服务尚未初始化")
    try:
        kg = getattr(_service, "kg", None)
        if kg is None:
            raise HTTPException(status_code=404, detail="知识图谱未初始化")

        from learning_path.path_builder import PathBuilder
        from learning_path.propagation import KnowledgePropagation
        from knowledge_graph.graph_query import GraphQuery

        query_engine = GraphQuery(kg)
        builder = PathBuilder(kg, query_engine)
        history = request.history or []

        # 1. 构建基础学习路径
        path = builder.build_path(
            user_id=request.user_id,
            user_history=history,
            target_topic=request.target_topic,
            max_nodes=request.max_nodes,
        )

        # 2. 知识掌握度传播（基于用户历史阅读）
        propagation = KnowledgePropagation(kg)
        if history:
            propagation.batch_update(history)

        # 3. 将掌握度应用到路径节点
        propagation.apply_to_path(path)

        # 4. 生成颜色映射和发光强度
        node_ids = [n.node_id for n in path.nodes]
        colors = propagation.get_color_mapping(node_ids)
        glows = propagation.get_glow_intensity(node_ids)

        # 5. 序列化返回
        result = builder.to_dict(path)
        for node in result["nodes"]:
            nid = node["node_id"]
            node["color"] = colors.get(nid, "#3B82F6")
            node["glow_intensity"] = round(glows.get(nid, 0.0), 4)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"学习路径生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"学习路径生成异常: {str(e)}")


# ── 启动入口 ──────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=" * 60)
    print("  科研推荐系统 REST API 启动")
    print("  文档地址: http://localhost:8000/docs")
    print("  Spring Boot 对接: POST http://localhost:8000/recommend")
    print("=" * 60)
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,         # 开发模式热重载
        log_level="info",
    )
