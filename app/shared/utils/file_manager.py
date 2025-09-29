"""
文件管理工具类
处理文件上传、保存、删除等操作
"""

import os
import uuid
from typing import Tuple, Optional
from pathlib import Path
from loguru import logger

from app.config import settings


class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.input_dir = Path(settings.input_dir)
        self.output_dir = Path(settings.output_dir)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (self.input_dir / "avatars").mkdir(exist_ok=True)
        (self.input_dir / "redesign_projects").mkdir(exist_ok=True)
        (self.input_dir / "posts").mkdir(exist_ok=True)
        (self.output_dir / "redesign_projects").mkdir(exist_ok=True)
        (self.output_dir / "steps").mkdir(exist_ok=True)
    
    def save_uploaded_file(
        self, 
        content: bytes, 
        filename: str, 
        task_id: str,
        category: str = "redesign_projects"
    ) -> Tuple[str, str]:
        """
        保存上传的文件
        
        Args:
            content: 文件内容
            filename: 原始文件名
            task_id: 任务ID
            category: 文件分类
            
        Returns:
            Tuple[str, str]: (文件路径, 公开URL)
        """
        try:
            # 获取文件扩展名
            file_extension = Path(filename).suffix or '.jpg'
            
            # 生成新文件名
            new_filename = f"{task_id}_{filename}"
            
            # 确定保存路径
            if category == "avatars":
                save_dir = self.input_dir / "avatars"
            elif category == "posts":
                save_dir = self.input_dir / "posts"
            else:
                save_dir = self.input_dir / "redesign_projects"
            
            file_path = save_dir / new_filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 生成公开URL
            public_url = f"/static/input/{category}/{new_filename}"
            
            logger.info(f"文件已保存: {file_path}")
            return str(file_path), public_url
            
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise Exception(f"文件保存失败: {str(e)}")
    
    def save_output_file(
        self, 
        content: bytes, 
        task_id: str, 
        file_type: str,
        step_number: Optional[int] = None
    ) -> str:
        """
        保存输出文件
        
        Args:
            content: 文件内容
            task_id: 任务ID
            file_type: 文件类型 (final, step, visualization)
            step_number: 步骤编号（仅用于步骤文件）
            
        Returns:
            str: 文件路径
        """
        try:
            # 生成文件名
            if file_type == "final":
                filename = f"{task_id}_final.jpg"
            elif file_type == "step":
                filename = f"{task_id}_step_{step_number}.jpg"
            elif file_type == "visualization":
                filename = f"{task_id}_viz_{step_number}.jpg"
            else:
                filename = f"{task_id}_{file_type}.jpg"
            
            # 确定保存目录
            if file_type == "step" or file_type == "visualization":
                save_dir = self.output_dir / "steps"
            else:
                save_dir = self.output_dir / "redesign_projects"
            
            file_path = save_dir / filename
            
            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"输出文件已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"输出文件保存失败: {str(e)}")
            raise Exception(f"输出文件保存失败: {str(e)}")
    
    def get_public_url(self, file_path: str) -> str:
        """获取公开访问URL"""
        try:
            path = Path(file_path)
            
            # 根据路径确定URL
            if "input" in str(path):
                relative_path = path.relative_to(self.input_dir)
                return f"/static/input/{relative_path}"
            elif "output" in str(path):
                relative_path = path.relative_to(self.output_dir)
                return f"/output/{relative_path}"
            else:
                return f"/output/{path.name}"
                
        except Exception as e:
            logger.error(f"生成公开URL失败: {str(e)}")
            return f"/output/{Path(file_path).name}"
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"文件已删除: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """清理旧文件"""
        try:
            import time
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # 清理输出目录
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"已删除旧文件: {file_path}")
            
            logger.info("文件清理完成")
            
        except Exception as e:
            logger.error(f"文件清理失败: {str(e)}")
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            path = Path(file_path)
            if path.exists():
                stat = path.stat()
                return {
                    "filename": path.name,
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "extension": path.suffix
                }
            else:
                return {}
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return {}
