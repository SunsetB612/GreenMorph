#!/usr/bin/env python3
"""
测试图片上传API的脚本
验证图片是否正确保存到文件夹和数据库
"""

import requests
import os
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000/api/redesign"

def test_image_upload():
    """测试图片上传功能"""
    
    # 检查测试图片是否存在
    test_image_path = Path("test_images/old_chair.jpg")
    if not test_image_path.exists():
        print(f"❌ 测试图片不存在: {test_image_path}")
        return False
    
    print("🚀 开始测试图片上传API...")
    
    try:
        # 上传图片
        with open(test_image_path, 'rb') as f:
            files = {'file': ('old_chair.jpg', f, 'image/jpeg')}
            response = requests.post(f"{BASE_URL}/analyze/image", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 图片上传成功!")
            print(f"   - 原始文件名: {result.get('uploaded_file')}")
            print(f"   - 保存路径: {result.get('file_path')}")
            print(f"   - 输入编号: {result.get('input_number')}")
            print(f"   - 识别物体: {result.get('main_objects', [])}")
            
            # 验证文件是否真的保存了
            file_path = result.get('file_path')
            if file_path and os.path.exists(file_path):
                print(f"✅ 文件已成功保存到: {file_path}")
                file_size = os.path.getsize(file_path)
                print(f"   - 文件大小: {file_size} 字节")
                
                # 检查是否保存到了正确的用户目录
                if "static/user1/input/" in file_path:
                    print("✅ 文件保存到了正确的用户目录 (static/user1/input/)")
                    
                    # 检查文件名是否包含有意义的前缀
                    filename = os.path.basename(file_path)
                    if any(obj in filename.lower() for obj in ["chair", "table", "furniture", "椅子", "桌子"]):
                        print("✅ 文件名包含有意义的物体标识")
                    else:
                        print(f"ℹ️  文件名: {filename}")
                else:
                    print("⚠️  文件未保存到预期的用户目录")
            else:
                print(f"❌ 文件未找到: {file_path}")
            
            return True
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_get_images():
    """测试获取图片列表API"""
    
    print("\n🔍 测试获取图片列表API...")
    
    try:
        response = requests.get(f"{BASE_URL}/images")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 获取图片列表成功!")
            print(f"   - 图片总数: {result.get('total', 0)}")
            
            images = result.get('images', [])
            for i, image in enumerate(images):
                print(f"   图片 {i+1}:")
                print(f"     - ID: {image.get('id')}")
                print(f"     - 文件名: {image.get('original_filename')}")
                print(f"     - 大小: {image.get('input_image_size')} 字节")
                print(f"     - 类型: {image.get('mime_type')}")
                print(f"     - 创建时间: {image.get('created_at')}")
            
            return True
        else:
            print(f"❌ 获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("GreenMorph 图片上传功能测试")
    print("=" * 50)
    
    # 测试图片上传
    upload_success = test_image_upload()
    
    # 测试获取图片列表
    list_success = test_get_images()
    
    print("\n" + "=" * 50)
    if upload_success and list_success:
        print("🎉 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    print("=" * 50)

if __name__ == "__main__":
    main()
