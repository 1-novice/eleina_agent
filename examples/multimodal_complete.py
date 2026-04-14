"""多模态功能完整示例 - 图片Base64输入 + 语音文件输入 + 语音输出"""
import sys
import os
import base64
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multimodal import MultimodalProcessor
from src.agent.execution_controller import execution_controller


def image_to_base64(image_path_or_url: str) -> str:
    """将图片（本地文件或URL）转换为base64编码"""
    try:
        # 判断是本地文件还是URL
        if image_path_or_url.startswith(('http://', 'https://')):
            # URL地址
            response = requests.get(image_path_or_url)
            response.raise_for_status()
            print(f"从URL下载图片: {image_path_or_url}")
            return base64.b64encode(response.content).decode("utf-8")
        else:
            # 本地文件路径
            if os.path.exists(image_path_or_url):
                with open(image_path_or_url, "rb") as f:
                    print(f"读取本地图片: {image_path_or_url}")
                    return base64.b64encode(f.read()).decode("utf-8")
            else:
                print(f"本地文件不存在: {image_path_or_url}")
                return ""
    except Exception as e:
        print(f"处理图片失败: {e}")
        return ""


def configure_processor():
    """配置多模态处理器"""
    processor = MultimodalProcessor()
    
    # 配置API密钥（从环境变量读取或直接配置）
    processor.configure({
        "enabled": True,
        "image_to_text": {
            "api_key": os.getenv("IMAGE_TO_TEXT_API_KEY"),
            "model": "qwen-vl-max"
        },
        "speech_to_text": {
            "api_key": os.getenv("SPEECH_TO_TEXT_API_KEY"),
            "api_secret": os.getenv("SPEECH_TO_TEXT_API_SECRET")
        },
        "text_to_speech": {
            "api_key": os.getenv("TEXT_TO_SPEECH_API_KEY"),
            "api_secret": os.getenv("TEXT_TO_SPEECH_API_SECRET")
        }
    })
    
    return processor


def test_image_input_base64(processor):
    """方案：图片Base64输入"""
    print("\n" + "=" * 60)
    print("方案: 图片Base64输入")
    print("=" * 60)
    
    # 示例图片（支持本地文件或URL）
    image_path = r"D:\yln.png"
    
    # 将图片转换为base64
    base64_image = image_to_base64(image_path)
    
    if not base64_image:
        print("图片下载失败，跳过测试")
        return ""
    
    print(f"图片已转换为Base64，长度: {len(base64_image)} 字符")
    
    # 增强用户消息（使用base64格式）
    user_message = "请描述这张图片里的产品"
    enhanced_input = processor.enhance_user_message(
        user_message=user_message,
        images=[{"data": base64_image, "type": "base64"}]
    )
    
    print(f"\n原始消息: {user_message}")
    print(f"\n增强后的输入:\n{enhanced_input}")
    
    return enhanced_input


def test_speech_input_file(processor):
    """方案A：语音文件输入"""
    print("\n" + "=" * 60)
    print("方案A: 语音文件输入")
    print("=" * 60)
    
    # 示例音频文件路径（使用原始字符串避免转义问题）
    audio_path = r"D:\python.learn\agent\test_audio.wav"
    
    if os.path.exists(audio_path):
        # 处理语音文件
        text = processor.process_input({
            "speech": {
                "data": audio_path,
                "type": "file",
                "format": "wav"
            }
        })
        
        print(f"音频文件: {audio_path}")
        print(f"识别结果: {text}")
        return text
    else:
        print(f"提示: 请将测试音频文件保存为 {audio_path}")
        return "这是测试语音转文本的结果"


def test_speech_output_basic(processor, text):
    """语音输出方式A：直接获取音频数据"""
    print("\n" + "=" * 60)
    print("语音输出方式A: 直接获取音频数据")
    print("=" * 60)
    
    # 方式A：直接获取音频数据
    audio_data = processor.process_output(text, output_mode="speech")
    
    if audio_data:
        # 保存到文件
        output_file = "output_speech_basic.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"语音文件已保存: {output_file}")
        return True
    else:
        print("提示: 请先配置TTS服务密钥")
        return False


def test_speech_output_custom(processor, text):
    """语音输出方式B：自定义音色和语速"""
    print("\n" + "=" * 60)
    print("语音输出方式B: 自定义音色和语速")
    print("=" * 60)
    
    # 方式B：自定义参数
    audio_data = processor.tts_processor.process(
        text=text,
        voice="female",    # female/male/child
        rate=0,           # 语速: -500~500
        volume=50,        # 音量: 0~100
        output_format="mp3"
    )
    
    if audio_data:
        # 保存到文件
        output_file = "output_speech_custom.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"语音文件已保存: {output_file}")
        print(f"配置参数: voice=female, rate=0, volume=50")
        return True
    else:
        print("提示: 请先配置TTS服务密钥")
        return False


def full_workflow(processor):
    """完整多模态对话流程"""
    print("\n" + "=" * 60)
    print("完整多模态对话流程")
    print("=" * 60)
    
    # 1. 用户输入（图片Base64 + 文本）
    # 使用可靠的测试图片URL
    image_url = r"D:\yln.png"
    user_text = "这张图片里有什么？"
    
    print(f"\n用户输入: {user_text}")
    print(f"图片URL: {image_url}")
    
    # 将图片转换为base64
    print("正在处理图片...")
    base64_image = image_to_base64(image_url)
    
    if not base64_image:
        print("图片下载失败，使用纯文本进行对话")
        enhanced_input = user_text
    else:
        print(f"图片已转换为Base64")
        # 2. 增强输入（图片转文本）
        enhanced_input = processor.enhance_user_message(
            user_message=user_text,
            images=[{"data": base64_image, "type": "base64"}]
        )
    
    # 3. 传入Agent处理
    print("\n正在处理...")
    context = {"user_id": "test_user", "session_id": "test_session"}
    result = execution_controller.execute(enhanced_input, context)
    answer = result.get("answer", "处理完成")
    
    print(f"Agent回答: {answer}")
    
    # 4. 语音输出（两种方式）
    test_speech_output_basic(processor, answer)
    test_speech_output_custom(processor, answer)
    
    print("\n✓ 完整流程执行完成！")


if __name__ == "__main__":
    print("=" * 60)
    print("多模态功能完整示例")
    print("=" * 60)
    
    # 配置处理器
    processor = configure_processor()
    
    # 测试各个功能
    test_image_input_base64(processor)
    test_speech_input_file(processor)
    
    # 测试语音输出（使用测试文本）
    test_text = "你好，我是伊蕾娜，很高兴为您服务！"
    test_speech_output_basic(processor, test_text)
    test_speech_output_custom(processor, test_text)
    
    # 完整流程演示
    full_workflow(processor)
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)