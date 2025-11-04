"""
使用预生成向量的知识库查询模块

这个版本使用 DashScope text-embedding-v4 模型生成的向量
"""

import numpy as np
import json
import os
import sys
from typing import List, Dict, Tuple
import dashscope
from http import HTTPStatus

# 处理导入
try:
    from . import agents_config
except ImportError:
    # 如果相对导入失败，尝试直接导入（用于测试）
    import agents_config

# 设置 API Key
dashscope.api_key = agents_config.dashscope_api_key


# 全局知识库存储
class KnowledgeBase:
    def __init__(self, use_precomputed: bool = True):
        """
        初始化知识库
        
        Args:
            use_precomputed: 是否使用预计算的向量文件
        """
        self.knowledge_items: List[Dict] = []
        self.use_precomputed = use_precomputed
        self.vector_model = "text-embedding-v4"
        self.load_knowledge()
    
    def vectorize_text(self, text: str) -> np.ndarray:
        """
        使用 DashScope text-embedding-v4 对文本进行向量化
        
        Args:
            text: 输入文本
            
        Returns:
            向量数组
        """
        try:
            resp = dashscope.TextEmbedding.call(
                model=self.vector_model,
                input=text,
            )
            
            if resp.status_code == HTTPStatus.OK:
                embedding = resp.output['embeddings'][0]['embedding']
                return np.array(embedding)
            else:
                print(f"✗ 向量化失败: {resp.code} - {resp.message}")
                return None
                
        except Exception as e:
            print(f"✗ 向量化出错: {e}")
            return None
    
    def load_knowledge(self):
        """加载知识库（优先使用预计算的向量文件）"""
        kb_dir = os.path.join(os.path.dirname(__file__), 'kb_data')
        vector_file = os.path.join(kb_dir, 'knowledge_vectors.json')
        jsonl_file = os.path.join(kb_dir, 'knowledge_permission.jsonl')
        
        # 尝试加载预计算的向量文件
        if self.use_precomputed and os.path.exists(vector_file):
            try:
                with open(vector_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for item in data['data']:
                    self.knowledge_items.append({
                        'content': item['content'],
                        'permission': item['permission'],
                        'vector': np.array(item['vector'])
                    })
                
                print(f"✓ 成功加载预计算向量文件: {len(self.knowledge_items)} 条记录")
                print(f"  模型: {data.get('model', 'unknown')}")
                print(f"  向量维度: {data.get('vector_dimension', 'unknown')}")
                for item in self.knowledge_items:
                    print(f"  - 内容: {item['content']}, 权限: {item['permission']}")
                return
                
            except Exception as e:
                print(f"✗ 加载向量文件失败: {e}")
                print("  回退到实时向量化模式...")
        
        # 回退：从 JSONL 文件加载并实时向量化
        if not os.path.exists(jsonl_file):
            print(f"警告: 知识库文件不存在: {jsonl_file}")
            return
        
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    item = json.loads(line)
                    content = item.get('content', '')
                    permission = item.get('permission', '')
                    
                    # 实时向量化内容
                    print(f"  正在向量化: {content}")
                    vector = self.vectorize_text(content)
                    
                    if vector is not None:
                        self.knowledge_items.append({
                            'content': content,
                            'permission': permission,
                            'vector': vector
                        })
            
            print(f"✓ 成功加载并向量化 {len(self.knowledge_items)} 条知识库记录")
            for item in self.knowledge_items:
                print(f"  - 内容: {item['content']}, 权限: {item['permission']}")
                
        except Exception as e:
            print(f"加载知识库失败: {e}")
    
    def compute_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            余弦相似度 (0-1之间，越大越相似)
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def search(self, query: str, user: str) -> Tuple[str, float]:
        """
        搜索知识库
        
        业务逻辑：
        1. 先不考虑权限，在所有知识中找到最匹配的内容
        2. 检查最匹配的内容是否有权限访问
        3. 如果有权限则返回，如果没有权限则返回权限错误
        
        Args:
            query: 查询文本
            user: 当前用户
            
        Returns:
            (最匹配的内容或错误信息, 相似度分数)
        """
        if not self.knowledge_items:
            return "知识库为空", 0.0
        
        # 向量化查询
        query_vector = self.vectorize_text(query)
        
        if query_vector is None:
            return "查询向量化失败", 0.0
        
        # 计算所有知识项的相似度（不考虑权限）
        similarities = []
        for item in self.knowledge_items:
            # 计算余弦相似度
            similarity = self.compute_cosine_similarity(query_vector, item['vector'])
            similarities.append({
                'content': item['content'],
                'similarity': similarity,
                'permission': item['permission']
            })
        
        # 按相似度降序排列
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # 获取最匹配的第一条
        best_match = similarities[0]
        print(f"  → 最佳匹配: {best_match['content']} (相似度: {best_match['similarity']:.4f}, 权限: {best_match['permission']})")
        
        # 检查权限
        if best_match['permission'] != user:
            error_msg = f"用户 {user} 没有访问权限（需要权限: {best_match['permission']}）"
            print(f"  ✗ 权限不足: {error_msg}")
            return error_msg, best_match['similarity']
        
        # 有权限，返回内容
        print(f"  ✓ 权限验证通过")
        return best_match['content'], best_match['similarity']


# 初始化全局知识库（使用预计算向量）
kb = KnowledgeBase(use_precomputed=True)


def getCurrentUserInfo():
    return 'testUser'



def collect_self_info(user_input):
    """
    收集本尊信息，通过向量匹配知识库
    
    Args:
        user_input: 用户输入
        
    Returns:
        匹配到的知识库内容
    """
    print(f'-----> collect_self_info in \n{user_input}\n')
    
    # 获取当前用户
    current_user = getCurrentUserInfo()
    print(f"  当前用户: {current_user}")
    
    # 在知识库中搜索
    best_match, similarity = kb.search(user_input, current_user)
    
    result = f'本尊信息获取成功，匹配结果：{best_match} (相似度: {similarity:.4f})'
    print(f'-----> collect_self_info out \n{result}\n')
    
    return result


function_mapper = {
    "本尊的个人信息获取工具": collect_self_info,
}


if __name__ == '__main__':
    # 测试代码
    print("\n" + "="*50)
    print("测试知识库向量匹配 (使用预计算向量)")
    print("="*50 + "\n")
    
    # 测试用例1: testUser的查询
    print("【测试1】testUser 查询 '我多大了'")
    result1 = collect_self_info("我多大了")
    print(f"结果: {result1}\n")
    
    # 测试用例2: testUser的另一个查询
    print("【测试2】testUser 查询 '年龄'")
    result2 = collect_self_info("年龄")
    print(f"结果: {result2}\n")
    
    # 测试用例3: 切换用户到qgao2
    print("【测试3】切换用户到 qgao2，查询 '性别是什么'")
    # 临时修改用户
    original_func = getCurrentUserInfo
    globals()['getCurrentUserInfo'] = lambda: 'qgao2'
    
    result3 = collect_self_info("性别是什么")
    print(f"结果: {result3}\n")
    
    # 测试用例4: testUser 查询关于性别的问题（应该匹配到qgao2的数据，但没有权限）
    print("【测试4】testUser 查询 '性别' (测试权限不足的情况)")
    globals()['getCurrentUserInfo'] = original_func  # 恢复为testUser
    
    result4 = collect_self_info("性别")
    print(f"结果: {result4}\n")
    
    # 测试用例5: qgao2 查询关于年龄的问题（应该匹配到testUser的数据，但没有权限）
    print("【测试5】qgao2 查询 '年龄' (测试权限不足的情况)")
    globals()['getCurrentUserInfo'] = lambda: 'qgao2'
    
    result5 = collect_self_info("多少岁")
    print(f"结果: {result5}\n")
    
    # 恢复原函数
    globals()['getCurrentUserInfo'] = original_func

