"""
改造项目API路由
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/projects")
async def get_projects():
    """获取用户的改造项目列表"""
    pass


@router.post("/projects")
async def create_project():
    """创建改造项目"""
    pass


@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    """获取单个改造项目"""
    pass


@router.put("/projects/{project_id}")
async def update_project(project_id: int):
    """更新改造项目"""
    pass


@router.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """删除改造项目"""
    pass


@router.post("/projects/{project_id}/analyze")
async def analyze_project(project_id: int):
    """分析改造项目"""
    pass


@router.post("/projects/{project_id}/generate")
async def generate_redesign(project_id: int):
    """生成改造方案"""
    pass
