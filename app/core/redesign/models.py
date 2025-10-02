"""
改造项目数据模型
"""

from sqlalchemy import Column, BigInteger, String, ForeignKey, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class InputImage(Base):
    """用户输入图片模型"""
    __tablename__ = "input_images"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255))
    input_image_path = Column(String(500), nullable=False)
    input_image_size = Column(Integer)
    mime_type = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class InputDemand(Base):
    """用户输入需求模型"""
    __tablename__ = "input_demand"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    demand = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RedesignProject(Base):
    """改造项目模型"""
    __tablename__ = "redesign_projects"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    project_name = Column(String(200), nullable=False)
    input_image_id = Column(BigInteger, ForeignKey("input_images.id"), nullable=True)
    input_demand_id = Column(BigInteger, ForeignKey("input_demand.id"), nullable=True)
    output_image_path = Column(String(500))
    output_pdf_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RedesignStep(Base):
    """改造步骤模型"""
    __tablename__ = "redesign_steps"
    
    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("redesign_projects.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    step_image_path = Column(String(500))


class ProjectDetail(Base):
    """项目详情模型"""
    __tablename__ = "project_details"
    
    id = Column(BigInteger, primary_key=True, index=True)
    project_id = Column(BigInteger, ForeignKey("redesign_projects.id"), nullable=False)
    total_cost_estimate = Column(Text)
    total_time_estimate = Column(Text)
    difficulty_level = Column(String(20))
    materials_and_tools = Column(Text)
    safety_notes = Column(Text)
    tips = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
