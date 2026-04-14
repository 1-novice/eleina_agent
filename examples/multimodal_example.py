"""多模态模块使用示例"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import base64
from src.multimodal import MultimodalProcessor


def example_image_to_text():
    """示例1: 图片转文本"""
    print("=" * 60)
    print("示例1: 图片转文本")
    print("=" * 60)
    
    # 初始化处理器
    processor = MultimodalProcessor()
    
    # 方式1: 使用图片文件路径
    print("\n1. 使用文件路径:")
    image_path = "test_image.png"  # 替换为您的图片路径
    if os.path.exists(image_path):
        result = processor.enhance_user_message(
            user_message="请描述这张图片的内容",
            images=[{"data": image_path, "type": "path"}]
        )
        print(f"增强后的输入:\n{result}")
    else:
        print(f"提示: 请将测试图片保存为 {image_path}")
    
    # 方式2: 使用base64编码
    print("\n2. 使用Base64编码:")
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        result = processor.enhance_user_message(
            user_message="请分析这张图片",
            images=[{"data": base64_image, "type": "base64"}]
        )
        print(f"增强后的输入:\n{result[:200]}...")  # 截断显示
    
    # 方式3: 使用图片URL
    print("\n3. 使用图片URL:")
    image_url = "https://example.com/image.png"  # 替换为真实图片URL
    result = processor.enhance_user_message(
        user_message="请描述这张图片",
        images=[{"data": image_url, "type": "url"}]
    )
    print(f"增强后的输入:\n{result}")


def example_speech_to_text():
    """示例2: 语音转文本"""
    print("\n" + "=" * 60)
    print("示例2: 语音转文本")
    print("=" * 60)
    
    processor = MultimodalProcessor()
    
    # 使用语音文件
    audio_path = "test_audio.wav"  # 替换为您的音频文件路径
    if os.path.exists(audio_path):
        result = processor.process_input({
            "speech": {"data": audio_path, "type": "file", "format": "wav"}
        })
        print(f"识别结果: {result}")
    else:
        print(f"提示: 请将测试音频保存为 {audio_path}")


def example_text_to_speech():
    """示例3: 文本转语音"""
    print("\n" + "=" * 60)
    print("示例3: 文本转语音")
    print("=" * 60)
    
    processor = MultimodalProcessor()
    
    # 生成语音
    text = "你好，我是伊蕾娜，很高兴为您服务！"
    audio_data = processor.process_output(text, output_mode="speech")
    
    if audio_data:
        # 保存到文件
        output_file = "output_speech.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"语音已保存到: {output_file}")
    else:
        print("提示: 请先配置TTS服务密钥")


def example_integration_with_agent():
    """示例4: 与Agent集成"""
    print("\n" + "=" * 60)
    print("示例4: 与Agent集成")
    print("=" * 60)
    
    from src.agent.execution_controller import execution_controller
    
    # 初始化多模态处理器
    processor = MultimodalProcessor()
    
    # 模拟用户输入（带图片）
    user_query = "这张图片里的产品是什么？"
    images = [
        {"data": "product_image.png", "type": "path"}  # 用户上传的图片
    ]
    
    # 步骤1: 增强用户输入（前置层）
    enhanced_input = processor.enhance_user_message(user_query, images)
    print(f"增强后的用户输入:\n{enhanced_input[:200]}...")
    
    # 步骤2: 传入Agent处理（核心逻辑完全复用）
    context = {"user_id": "test_user", "session_id": "test_session"}
    result = execution_controller.execute(enhanced_input, context)
    
    # 步骤3: 处理输出（后置层）
    answer = result.get("answer", "处理完成")
    print(f"\nAgent回答: {answer}")
    
    # 可选：转为语音
    audio_output = processor.process_output(answer, output_mode="speech")
    if audio_output:
        print("已生成语音输出")


if __name__ == "__main__":
    print("=" * 60)
    print("多模态模块使用示例")
    print("=" * 60)
    
    # 运行各个示例
    example_image_to_text()
    example_speech_to_text()
    example_text_to_speech()
    example_integration_with_agent()
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)