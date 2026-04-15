import subprocess
result = subprocess.run(
    ['poetry', 'run', 'python', 'test_all_features.py'],
    capture_output=True,
    text=True
)
with open('test_result.txt', 'w', encoding='utf-8') as f:
    f.write('STDOUT:\n')
    f.write(result.stdout)
    f.write('\nSTDERR:\n')
    f.write(result.stderr)
print('测试结果已保存到 test_result.txt')