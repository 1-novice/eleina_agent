"""图像多模态功能完整示例 - 独立无状态设计，支持流式输出"""
import sys
import os
import base64
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def image_to_base64(image_path_or_url: str) -> str:
    """将图片转换为base64编码"""
    try:
        if image_path_or_url.startswith(('http://', 'https://')):
            response = requests.get(image_path_or_url)
            response.raise_for_status()
            print(f"从URL下载图片: {image_path_or_url}")
            return base64.b64encode(response.content).decode("utf-8")
        else:
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
    """配置图像处理器"""
    from src.multimodal import ImageProcessor
    
    processor = ImageProcessor()
    
    processor.configure({
        "enabled": True,
        "image_to_text": {
            "api_key": os.getenv("IMAGE_TO_TEXT_API_KEY"),
            "model": "qwen-vl-plus"
        }
    })
    
    return processor


def full_workflow(processor, stream=True):
    """完整图像多模态对话流程"""
    print("\n" + "=" * 60)
    print("完整图像多模态对话流程")
    print(f"输出模式: {'流式输出' if stream else '普通输出'}")
    print("=" * 60)
    
    image_url = r"D:\jialuo.jpg"
    user_text = "这张图片里有什么？"
    
    print(f"\n用户输入: {user_text}")
    print(f"图片URL: {image_url}")
    
    if not os.path.exists(image_url):
        print(f"警告: 图片文件不存在: {image_url}")
        import glob
        jialuo_files = glob.glob(r"D:\jialuo.jpg")
        if jialuo_files:
            image_url = jialuo_files[0]
            print(f"使用替代图片: {image_url}")
        else:
            print("错误: 未找到图片文件")
            return
    
    file_size = os.path.getsize(image_url)
    file_mtime = os.path.getmtime(image_url)
    print(f"文件大小: {file_size} bytes")
    print(f"修改时间: {file_mtime}")
    
    print("\n正在处理图片...")
    base64_image = image_to_base64(image_url)
    
    if not base64_image:
        print("图片处理失败，使用纯文本进行对话")
        enhanced_input = user_text
    else:
        print(f"图片已转换为Base64，长度: {len(base64_image)}")
        
        print("\n正在进行图片描述...")
        enhanced_input = processor.enhance_message(
            user_message=user_text,
            images=[{"data": base64_image, "type": "base64"}]
        )
    
    print(f"\n增强后的输入:")
    print(enhanced_input)
    
    from src.agent.execution_controller import execution_controller
    
    print("\n正在处理...")
    context = {"user_id": "test_user", "session_id": "test_session", "stream": stream}
    
    if stream:
        print("Agent回答: ", end="", flush=True)
        full_answer = ""
        for chunk in execution_controller.execute_stream(enhanced_input, context):
            print(chunk, end="", flush=True)
            full_answer += chunk
        print()
    else:
        result = execution_controller.execute(enhanced_input, context)
        answer = result.get("answer", "处理完成")
        print(f"\nAgent回答: {answer}")
    
    print("\n✓ 完整流程执行完成！")


if __name__ == "__main__":
    print("=" * 60)
    print("图像多模态功能完整示例")
    print("=" * 60)
    
    processor = configure_processor()
    
    full_workflow(processor, stream=True)
    
    print("\n" + "=" * 60)
    print("示例执行完成！")
    print("=" * 60)