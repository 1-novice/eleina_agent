"""图像多模态模块使用示例 - 独立无状态设计"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
from src.multimodal import ImageProcessor


def example_image_to_text():
    """示例: 图片转文本"""
    print("=" * 60)
    print("示例: 图片转文本")
    print("=" * 60)
    
    processor = ImageProcessor()
    
    print("\n1. 使用文件路径:")
    image_path = "test_image.png"
    if os.path.exists(image_path):
        result = processor.enhance_message(
            user_message="请描述这张图片的内容",
            images=[{"data": image_path, "type": "path"}]
        )
        print(f"增强后的输入:\n{result}")
    else:
        print(f"提示: 请将测试图片保存为 {image_path}")
    
    print("\n2. 使用Base64编码:")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        result = processor.enhance_message(
            user_message="请分析这张图片",
            images=[{"data": base64_image, "type": "base64"}]
        )
        print(f"增强后的输入:\n{result[:200]}...")


def example_integration_with_agent():
    """示例: 与Agent集成"""
    print("\n" + "=" * 60)
    print("示例: 与Agent集成")
    print("=" * 60)
    
    from src.agent.execution_controller import execution_controller
    
    processor = ImageProcessor()
    
    user_query = "这张图片里的产品是什么？"
    images = [
        {"data": "product_image.png", "type": "path"}
    ]
    
    enhanced_input = processor.enhance_message(user_query, images)
    print(f"增强后的用户输入:\n{enhanced_input[:200]}...")
    
    context = {"user_id": "test_user", "session_id": "test_session"}
    result = execution_controller.execute(enhanced_input, context)
    
    answer = result.get("answer", "处理完成")
    print(f"\nAgent回答: {answer}")


if __name__ == "__main__":
    print("=" * 60)
    print("图像多模态模块使用示例")
    print("=" * 60)
    
    example_image_to_text()
    example_integration_with_agent()
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)