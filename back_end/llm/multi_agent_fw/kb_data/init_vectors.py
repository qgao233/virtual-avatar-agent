"""
知识库向量化初始化脚本

功能：
1. 读取 knowledge_permission.jsonl 文件
2. 使用 DashScope text-embedding-v4 模型对 content 进行向量化
3. 生成包含向量的映射文件 knowledge_vectors.json
"""

import json
import os
import sys
import dashscope
from http import HTTPStatus
import numpy as np

# 添加父目录到路径以便导入配置
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import model_config

# 设置 API Key
dashscope.api_key = model_config.dashscope_api_key


def vectorize_text(text: str, model: str = "text-embedding-v4") -> list:
    """
    使用 DashScope 对文本进行向量化
    
    Args:
        text: 要向量化的文本
        model: 使用的模型名称
        
    Returns:
        向量列表
    """
    try:
        resp = dashscope.TextEmbedding.call(
            model=model,
            input=text,
        )
        
        if resp.status_code == HTTPStatus.OK:
            # 提取向量
            embedding = resp.output['embeddings'][0]['embedding']
            print(f"✓ 成功向量化: '{text}' (维度: {len(embedding)})")
            return embedding
        else:
            print(f"✗ 向量化失败: {resp.code} - {resp.message}")
            return None
            
    except Exception as e:
        print(f"✗ 向量化出错: {e}")
        return None


def init_knowledge_vectors(input_file: str = "knowledge_permission.jsonl", 
                          output_file: str = "knowledge_vectors.json"):
    """
    初始化知识库向量
    
    Args:
        input_file: 输入的知识库文件
        output_file: 输出的向量文件
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, output_file)
    
    print("="*60)
    print("知识库向量化初始化")
    print("="*60)
    print(f"输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"向量模型: text-embedding-v4")
    print("="*60 + "\n")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        print(f"✗ 错误: 输入文件不存在: {input_path}")
        return
    
    # 读取知识库
    knowledge_items = []
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    item = json.loads(line)
                    knowledge_items.append(item)
                except json.JSONDecodeError as e:
                    print(f"✗ 警告: 第 {line_num} 行 JSON 解析失败: {e}")
                    
        print(f"✓ 成功读取 {len(knowledge_items)} 条知识库记录\n")
        
    except Exception as e:
        print(f"✗ 读取文件失败: {e}")
        return
    
    # 向量化每条知识
    vectorized_data = []
    success_count = 0
    
    for idx, item in enumerate(knowledge_items, 1):
        content = item.get('content', '')
        permission = item.get('permission', '')
        
        print(f"[{idx}/{len(knowledge_items)}] 处理: {content} (权限: {permission})")
        
        if not content:
            print(f"  ✗ 跳过: 内容为空")
            continue
        
        # 向量化
        vector = vectorize_text(content)
        
        if vector is not None:
            vectorized_data.append({
                'content': content,
                'permission': permission,
                'vector': vector,
                'vector_dim': len(vector)
            })
            success_count += 1
        else:
            print(f"  ✗ 向量化失败，跳过该条记录")
        
        print()
    
    # 保存结果
    if vectorized_data:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'model': 'text-embedding-v4',
                    'total_count': len(vectorized_data),
                    'vector_dimension': vectorized_data[0]['vector_dim'] if vectorized_data else 0,
                    'data': vectorized_data
                }, f, ensure_ascii=False, indent=2)
            
            print("="*60)
            print(f"✓ 向量化完成!")
            print(f"  - 总记录数: {len(knowledge_items)}")
            print(f"  - 成功向量化: {success_count}")
            print(f"  - 向量维度: {vectorized_data[0]['vector_dim']}")
            print(f"  - 输出文件: {output_path}")
            print("="*60)
            
            # 显示统计信息
            print("\n知识库统计:")
            permission_stats = {}
            for item in vectorized_data:
                perm = item['permission']
                permission_stats[perm] = permission_stats.get(perm, 0) + 1
            
            for perm, count in permission_stats.items():
                print(f"  - {perm}: {count} 条")
            
        except Exception as e:
            print(f"✗ 保存文件失败: {e}")
    else:
        print("✗ 没有成功向量化的数据")


def test_vector_similarity():
    """
    测试向量相似度计算
    """
    print("\n" + "="*60)
    print("测试向量相似度")
    print("="*60 + "\n")
    
    # 读取向量文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    vector_file = os.path.join(script_dir, "knowledge_vectors.json")
    
    if not os.path.exists(vector_file):
        print("✗ 向量文件不存在，请先运行初始化")
        return
    
    with open(vector_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    knowledge_items = data['data']
    
    # 测试查询
    test_queries = ["我多大了", "年龄", "性别是什么"]
    
    for query in test_queries:
        print(f"查询: '{query}'")
        query_vector = vectorize_text(query)
        
        if query_vector is None:
            print("  ✗ 查询向量化失败\n")
            continue
        
        # 计算与所有知识的相似度
        similarities = []
        for item in knowledge_items:
            vector = np.array(item['vector'])
            query_vec = np.array(query_vector)
            
            # 计算余弦相似度
            cosine_sim = np.dot(query_vec, vector) / (np.linalg.norm(query_vec) * np.linalg.norm(vector))
            
            similarities.append({
                'content': item['content'],
                'permission': item['permission'],
                'similarity': cosine_sim
            })
        
        # 排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 显示结果
        print("  匹配结果:")
        for i, sim in enumerate(similarities[:3], 1):
            print(f"    {i}. {sim['content']} (相似度: {sim['similarity']:.4f}, 权限: {sim['permission']})")
        print()


if __name__ == '__main__':
    # 初始化向量
    init_knowledge_vectors()
    
    # 测试相似度
    test_vector_similarity()

