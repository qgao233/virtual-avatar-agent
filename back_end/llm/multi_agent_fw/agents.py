import json
import dashscope
from dashscope import Assistants, Messages, Runs, Threads
from qwen_agent.agents import Assistant

from .agents_functions import function_mapper
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import model_config

dashscope.api_key = model_config.dashscope_api_key
use_model = model_config.qwen_model

# 报销数据分析助手：对每一张报销单据或者行程单中的数据详情进行读取和抽取，准备后续使用，如果要对一张单据或者行程单进行数据抽取，则调用该agent；
planner_agent=Assistants.create(
    model=use_model,
    name='流程编排机器人',
    description='你是团队的leader，你的手下有很多agent，你需要根据用户的输入，决定要以怎样的顺序去使用这些agent',
    instructions="""你的团队中有以下agent。
        本尊信息智能体：如果提问中有问你的个人信息，其实就是问关于本尊信息获取的问题，则调用该agent；
        上网搜索智能体：如果提问中与问你的个人信息无关，则调用该agent进行上网搜索；

        你需要根据用户的问题，判断要使用哪些agent，以及以什么顺序使用这些agent，一个agent可以被多次调用。你的返回形式是一个列表，不能返回其它信息。比如：["本尊信息智能体", "上网搜索智能体"]，或者["本尊信息智能体", "上网搜索智能体", "本尊信息智能体"]，列表中的元素只能为上述的agent。"""
    )


print("Planner Agent创建完成")


self_info_agent = Assistants.create(
    model=use_model,
    name="本尊信息智能体",
    description="一个本尊信息获取智能体，能够根据用户输入，获取本尊的某些信息。",
    instructions='''你是一个本尊信息获取智能体，能够根据用户输入，获取本尊的某些信息。当你被调用时，请使用本尊的个人信息获取工具来获取本尊的某些信息。''',
    tools=[
        {
            'type': 'function',
            'function': {
                'name': '本尊的个人信息获取工具',
                'description': '当用户需要获取本尊的某些信息时比较有用。',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'user_input': {
                            'type': 'str',
                            'description': '用户输入'
                        },
                    },
                    'required': ['user_input']},
            }
        }
    ]
)
print(f'{self_info_agent.name}创建完成')

# tools = [{
#   "mcpServers": {
#     "open-websearch-local": {
#       "command": "node",
#       "args": ["C:/Users/qgao2/Desktop/科室/Salotto/251113/demo/back-end/llm/multi_agent_fw/mcp/open-webSearch-FORKED-main/build/index.js"],
#       "env": {
#         "MODE": "stdio",
#         "DEFAULT_SEARCH_ENGINE": "duckduckgo",
#         "ALLOWED_SEARCH_ENGINES": "duckduckgo,bing,exa"
#       }
#     }
#   }
# }]

# web_search_agent = Assistant(
#     name="上网搜索智能体",
#     llm={
#         'model': use_model,  # 使用通义千问3.0大模型
#         'model_server': 'dashscope'
#     },
#     system_message="你是一个上网搜索智能体，能够根据用户输入，进行上网搜索。",
#     function_list=tools  # 绑定MCP工具
# )
# print(f'{web_search_agent.name}创建完成')


web_search_agent = Assistants.create(
    model=use_model,
    name="上网搜索智能体",
    description="一个上网搜索智能体，能够根据用户输入，进行上网搜索。",
    instructions='''你是一个上网搜索智能体，能够根据用户输入，进行上网搜索。''',
    tools=[
        {
            'type': 'quark_search',
        }
    ]
)
print(f'{web_search_agent.name}创建完成')


summary_agent = Assistants.create(
    model=use_model,
    name="最终答案总结助手",
    description="一个智能助手，根据用户的问题与参考信息，全面、完整地回答用户问题。",
    instructions='''你是一个智能助手，根据用户的问题与其他助手反馈的参考信息，全面、完整地回答用户问题。''',
)
print(f'{summary_agent.name}创建完成')


# 将列表中的字符串映射到Agent对象上
# 将字符串格式的Agent名称映射到具体Agent对象
agent_mapper = {
    "本尊信息智能体": self_info_agent,
    "上网搜索智能体": web_search_agent,
}


# 输入message信息，输出为指定Agent的回复
def get_agent_response(assistant, message=''):
    # 打印出输入Agent的信息
    print(f"-----> Query in get_agent_response func is : {message}")
    thread = Threads.create()
    message = Messages.create(thread.id, content=message)
    run = Runs.create(thread.id, assistant_id=assistant.id)
    run_status = Runs.wait(run.id, thread_id=thread.id)
    # 如果响应失败，会打印出run failed
    if run_status.status == 'failed':
        print('run failed:')
    # 如果需要工具来辅助大模型输出，则进行以下流程
    if run_status.required_action:
        f = run_status.required_action.submit_tool_outputs.tool_calls[0].function
        # 获得function name
        func_name = f['name']
        # 获得function 的入参
        param = json.loads(f['arguments'])
        # 打印出工具信息
        print("-----> function is",f)
        # 根据function name，通过function_mapper映射到函数，并将参数输入工具函数得到output输出
        if func_name in function_mapper:
            output = function_mapper[func_name](**param)
        else:
            output = ""
        tool_outputs = [{
            'output':
                output
        }]
        run = Runs.submit_tool_outputs(run.id,
                                       thread_id=thread.id,
                                       tool_outputs=tool_outputs)
        run_status = Runs.wait(run.id, thread_id=thread.id)
    run_status = Runs.get(run.id, thread_id=thread.id)
    msgs = Messages.list(thread.id)
    # 将Agent的输出返回
    ret_msg = msgs['data'][0]['content'][0]['text']['value']
    return ret_msg

if __name__ == '__main__':
    user_query = input("请输入您的问题：")
    # print(f'user_query is {user_query}')
    print(get_agent_response(planner_agent, user_query))

