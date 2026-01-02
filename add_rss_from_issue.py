import os
import sys
import yaml
import json
import requests
from github import Github

# 从环境变量获取GitHub Token
token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("未找到GITHUB_TOKEN环境变量")
    sys.exit(1)

# 初始化GitHub客户端
g = Github(token)

# 获取Issue信息
issue_json = os.environ.get('GITHUB_EVENT_PATH')
if not issue_json:
    print("未找到GITHUB_EVENT_PATH环境变量")
    sys.exit(1)

with open(issue_json, 'r') as f:
    issue_data = json.load(f)

# 获取Issue基本信息
repo_name = issue_data['repository']['full_name']
issue_number = issue_data['issue']['number']
issue_title = issue_data['issue']['title']
issue_body = issue_data['issue']['body']
issue_state = issue_data['issue']['state']

# 只有当Issue是打开状态且标题包含"添加RSS源"时才处理
if issue_state != 'open' or '添加RSS源' not in issue_title:
    print(f"Issue #{issue_number} 不是打开状态或标题不包含'添加RSS源'，跳过处理")
    sys.exit(0)

# 解析Issue内容
# GitHub表单式issue模板提交的内容是结构化的，包含各种字段
# 我们需要从issue数据中提取表单字段，而不是解析文本内容
try:
    # 检查issue是否使用了模板
    if 'labels' in issue_data['issue']:
        labels = [label['name'] for label in issue_data['issue']['labels']]
        # 只有带有add-rss标签的issue才处理
        if 'add-rss' not in labels:
            print(f"Issue #{issue_number} 没有add-rss标签，跳过处理")
            sys.exit(0)
    
    # 从issue事件数据中提取表单字段
    # GitHub Actions事件数据中的issue.body是表单提交后的文本内容
    # 但我们需要从event数据中直接获取结构化的表单字段
    # 注意：GitHub Actions的issues事件不直接提供结构化的表单字段
    # 我们需要解析issue.body中的Markdown表格或列表
    
    body = issue_data['issue']['body']
    website_name = None
    rss_url = None
    
    # 解析表单式issue模板生成的Markdown内容
    # 表单式issue模板生成的内容格式如下：
    # ### 网站名称
    # 奇安信威胁情报中心
    # 
    # ### RSS URL
    # https://example.com/feed.xml
    
    lines = body.strip().split('\n')
    current_field = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('### '):
            # 字段标题
            current_field = line[4:].strip()
        elif current_field and line:
            # 字段值
            if current_field == '网站名称':
                website_name = line
            elif current_field == 'RSS URL':
                rss_url = line
            # 重置当前字段，避免重复赋值
            current_field = None
    
    # 如果上面的解析方法失败，尝试另一种格式（使用冒号分隔）
    if not website_name or not rss_url:
        for line in lines:
            line = line.strip()
            if line.startswith('网站名称:'):
                website_name = line.split(':', 1)[1].strip()
            elif line.startswith('RSS URL:'):
                rss_url = line.split(':', 1)[1].strip()
    
    # 如果还是失败，尝试原始的中文冒号格式
    if not website_name or not rss_url:
        for line in lines:
            line = line.strip()
            if line.startswith('网站名称：'):
                website_name = line.split('：')[1].strip()
            elif line.startswith('RSS链接：') or line.startswith('RSS URL：'):
                rss_url = line.split('：')[1].strip()
    
    if not website_name or not rss_url:
        raise ValueError("Issue内容格式不正确，无法提取网站名称或RSS链接")
    
    print(f"解析到的网站名称：{website_name}")
    print(f"解析到的RSS链接：{rss_url}")
    
except Exception as e:
    print(f"解析Issue内容失败：{str(e)}")
    # 回复Issue
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(number=issue_number)
    issue.create_comment(f"解析Issue内容失败：{str(e)}\n请按照正确格式提交：\n网站名称：XXX\nRSS链接：XXX")
    sys.exit(1)

# 读取现有的rss_dataleak.yaml文件
try:
    with open('rss_dataleak.yaml', 'r', encoding='utf-8') as f:
        rss_config = yaml.safe_load(f) or {}
    
except Exception as e:
    print(f"读取rss_dataleak.yaml文件失败：{str(e)}")
    sys.exit(1)

# 添加新的RSS源
rss_config[website_name] = {
    'rss_url': rss_url,
    'website_name': website_name
}

# 保存更新后的rss_dataleak.yaml文件
try:
    with open('rss_dataleak.yaml', 'w', encoding='utf-8') as f:
        yaml.dump(rss_config, f, allow_unicode=True, default_flow_style=False)
    print(f"成功将新RSS源添加到rss_dataleak.yaml")
    
except Exception as e:
    print(f"保存rss_dataleak.yaml文件失败：{str(e)}")
    sys.exit(1)

# 回复并关闭Issue
try:
    repo = g.get_repo(repo_name)
    issue = repo.get_issue(number=issue_number)
    issue.create_comment(f"成功添加RSS源：\n网站名称：{website_name}\nRSS链接：{rss_url}")
    issue.edit(state='closed')
    print(f"成功回复并关闭Issue #{issue_number}")
    
except Exception as e:
    print(f"回复或关闭Issue失败：{str(e)}")
    sys.exit(1)

print("处理完成！")
