"""批量添加角色图片到向量库"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.multimodal.character_recognizer import CharacterRecognizer
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("❌ 未配置DASHSCOPE_API_KEY")
        return
    
    recognizer = CharacterRecognizer(api_key=api_key)
    
    # 创建集合
    if not recognizer.create_collection():
        print("❌ 无法创建集合")
        return
    
    # 角色列表 - 用户可以在这里添加新角色
    # 请确保图片文件存在于指定路径
    characters = [
        {"name": 
            "伊雷娜", 
         "path": ["D:\\yln_rag\\yln1.png","D:\\yln_rag\\yln2.png","D:\\yln_rag\\yln3.png","D:\\yln_rag\\yln4.png","D:\\yln_rag\\yln5.png","D:\\yln_rag\\yln6.png",
         "D:\\yln_rag\\yln7.png","D:\\yln_rag\\yln8.png"]}
    ]
    
    print(f"开始添加 {len(characters)} 个角色...")
    
    success_count = recognizer.batch_add_characters(characters)
    
    print(f"\n添加完成！成功: {success_count}/{len(characters)}")
    print(f"向量库中角色总数: {recognizer.get_character_count()}")

if __name__ == "__main__":
    main()