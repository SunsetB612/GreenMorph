"""
改造风格和材料选择模型
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class RedesignStyle(str, Enum):
    """改造风格枚举"""
    MODERN = "modern"                    # 现代风格
    CONTEMPORARY = "contemporary"        # 当代风格
    MINIMALIST = "minimalist"            # 极简风格
    INDUSTRIAL = "industrial"            # 工业风格
    SCANDINAVIAN = "scandinavian"        # 北欧风格
    VINTAGE = "vintage"                  # 复古风格
    RUSTIC = "rustic"                    # 乡村风格
    BOHEMIAN = "bohemian"                # 波西米亚风格
    JAPANESE = "japanese"               # 日式风格
    MEDITERRANEAN = "mediterranean"      # 地中海风格
    ECO_FRIENDLY = "eco_friendly"        # 环保风格
    LUXURY = "luxury"                    # 奢华风格


class MaterialType(str, Enum):
    """材料类型枚举"""
    WOOD = "wood"                        # 木材
    METAL = "metal"                      # 金属
    FABRIC = "fabric"                    # 织物
    GLASS = "glass"                      # 玻璃
    CERAMIC = "ceramic"                  # 陶瓷
    PLASTIC = "plastic"                  # 塑料
    LEATHER = "leather"                  # 皮革
    BAMBOO = "bamboo"                    # 竹子
    STONE = "stone"                      # 石材
    RECYCLED = "recycled"                # 回收材料


class ColorScheme(str, Enum):
    """色彩方案枚举"""
    NEUTRAL = "neutral"                  # 中性色
    EARTH_TONES = "earth_tones"          # 大地色系
    PASTEL = "pastel"                    # 柔和色
    BOLD = "bold"                        # 大胆色
    MONOCHROME = "monochrome"            # 单色
    VIBRANT = "vibrant"                 # 鲜艳色
    NATURAL = "natural"                  # 自然色
    METALLIC = "metallic"               # 金属色


class StylePreference(BaseModel):
    """风格偏好设置"""
    primary_style: RedesignStyle         # 主要风格
    secondary_style: Optional[RedesignStyle] = None  # 次要风格
    materials: List[MaterialType] = []   # 材料偏好
    color_scheme: ColorScheme = ColorScheme.NEUTRAL  # 色彩方案
    budget_range: Optional[str] = None   # 预算范围
    time_constraint: Optional[str] = None  # 时间限制
    skill_level: Optional[str] = None   # 技能水平


class StyleDescription(BaseModel):
    """风格描述"""
    name: str                            # 风格名称
    description: str                     # 风格描述
    characteristics: List[str]           # 特征列表
    suitable_for: List[str]             # 适用场景
    materials: List[str]                # 常用材料
    colors: List[str]                   # 常用颜色
    difficulty: str                      # 难度等级
    time_estimate: str                  # 时间估算
    cost_estimate: str                  # 成本估算


# 预定义的风格描述
STYLE_DESCRIPTIONS = {
    RedesignStyle.MODERN: StyleDescription(
        name="现代风格",
        description="简洁、功能性强的设计，注重线条和几何形状",
        characteristics=["简洁线条", "几何形状", "功能性", "中性色调", "现代材料"],
        suitable_for=["客厅", "卧室", "办公室", "餐厅"],
        materials=["金属", "玻璃", "木材", "皮革"],
        colors=["白色", "黑色", "灰色", "银色"],
        difficulty="中等",
        time_estimate="2-4周",
        cost_estimate="中等"
    ),
    RedesignStyle.CONTEMPORARY: StyleDescription(
        name="当代风格",
        description="融合现代和传统元素，注重舒适性和实用性",
        characteristics=["舒适性", "实用性", "混合材料", "柔和色调", "个性化"],
        suitable_for=["家庭空间", "休闲区域", "多功能空间"],
        materials=["木材", "织物", "金属", "天然材料"],
        colors=["米色", "棕色", "蓝色", "绿色"],
        difficulty="中等",
        time_estimate="3-5周",
        cost_estimate="中等"
    ),
    RedesignStyle.MINIMALIST: StyleDescription(
        name="极简风格",
        description="追求最简化的设计，强调空间和光线",
        characteristics=["极简设计", "大量留白", "单一色调", "功能性", "整洁"],
        suitable_for=["小空间", "工作室", "现代住宅"],
        materials=["木材", "金属", "玻璃", "白色材料"],
        colors=["白色", "米色", "灰色", "黑色"],
        difficulty="简单",
        time_estimate="1-2周",
        cost_estimate="低"
    ),
    RedesignStyle.INDUSTRIAL: StyleDescription(
        name="工业风格",
        description="粗犷、原始的设计风格，强调材料和结构",
        characteristics=["粗犷外观", "原始材料", "金属元素", "裸露结构", "深色调"],
        suitable_for=["工作室", "阁楼", "现代空间"],
        materials=["金属", "混凝土", "砖块", "木材"],
        colors=["黑色", "灰色", "棕色", "银色"],
        difficulty="困难",
        time_estimate="4-6周",
        cost_estimate="高"
    ),
    RedesignStyle.SCANDINAVIAN: StyleDescription(
        name="北欧风格",
        description="简洁、自然、功能性的设计，强调舒适性",
        characteristics=["简洁设计", "自然材料", "舒适性", "浅色调", "功能性"],
        suitable_for=["家庭空间", "卧室", "客厅", "儿童房"],
        materials=["木材", "织物", "羊毛", "天然材料"],
        colors=["白色", "米色", "浅蓝色", "浅绿色"],
        difficulty="简单",
        time_estimate="2-3周",
        cost_estimate="中等"
    ),
    RedesignStyle.VINTAGE: StyleDescription(
        name="复古风格",
        description="怀旧、经典的设计，强调历史感和独特性",
        characteristics=["怀旧感", "经典设计", "独特元素", "温暖色调", "历史感"],
        suitable_for=["客厅", "书房", "收藏空间"],
        materials=["木材", "织物", "金属", "复古材料"],
        colors=["棕色", "米色", "金色", "深红色"],
        difficulty="困难",
        time_estimate="4-8周",
        cost_estimate="高"
    ),
    RedesignStyle.ECO_FRIENDLY: StyleDescription(
        name="环保风格",
        description="注重可持续性和环保材料的设计",
        characteristics=["环保材料", "可持续性", "自然元素", "绿色理念", "回收利用"],
        suitable_for=["所有空间", "户外区域", "绿色建筑"],
        materials=["回收材料", "竹子", "天然纤维", "环保涂料"],
        colors=["绿色", "棕色", "米色", "自然色"],
        difficulty="中等",
        time_estimate="3-4周",
        cost_estimate="中等"
    )
}


def get_style_description(style: RedesignStyle) -> StyleDescription:
    """获取风格描述"""
    return STYLE_DESCRIPTIONS.get(style, STYLE_DESCRIPTIONS[RedesignStyle.MODERN])


def get_all_styles() -> List[StyleDescription]:
    """获取所有风格描述"""
    return list(STYLE_DESCRIPTIONS.values())


def get_style_by_name(name: str) -> Optional[RedesignStyle]:
    """根据名称获取风格枚举"""
    for style in RedesignStyle:
        if style.value == name:
            return style
    return None
