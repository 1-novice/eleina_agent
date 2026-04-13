"""状态机功能测试"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components import state_machine


class TestStateMachine:
    """状态机测试类"""
    
    def test_state_machine_initialization(self):
        """测试状态机初始化"""
        assert state_machine is not None
        print(f"✓ 状态机初始化成功，当前状态: {state_machine.get_state().value}")
    
    def test_state_transitions(self):
        """测试状态转换"""
        # 重置状态机
        state_machine.reset()
        initial_state = state_machine.get_state().value
        print(f"✓ 初始状态: {initial_state}")
        
        # 执行一步
        state_machine.step()
        new_state = state_machine.get_state().value
        print(f"✓ 执行一步后状态: {new_state}")
        
        # 测试不同的状态转换参数
        state_machine.step(answer_generated=True)
        state_after_answer = state_machine.get_state().value
        print(f"✓ 生成答案后状态: {state_after_answer}")
    
    def test_state_machine_context(self):
        """测试状态机上下文"""
        # 设置上下文
        state_machine.context.update({
            "user_input": "测试问题",
            "session_id": "test_session"
        })
        
        # 获取上下文
        context = state_machine.context
        assert "user_input" in context
        assert "session_id" in context
        print(f"✓ 上下文设置成功: user_input={context.get('user_input')}")


if __name__ == "__main__":
    print("=" * 60)
    print("状态机功能测试")
    print("=" * 60)
    
    test = TestStateMachine()
    
    try:
        test.test_state_machine_initialization()
        test.test_state_transitions()
        test.test_state_machine_context()
        
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()