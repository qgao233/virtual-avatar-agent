from multi_agent_fw.agents import get_agent_response, planner_agent, agent_mapper, summary_agent
import ast

def get_multi_agent_response(query):
    # 获取Agent的运行顺序
    agent_order = get_agent_response(planner_agent, query)
    # 由于大模型输出可能不稳定，因此加入异常处理模块处理列表字符串解析失败的问题
    try:
        order_stk = ast.literal_eval(agent_order)
        print("Planner Agent正在工作：")
        for i in range(len(order_stk)):
            print(f'第{i + 1}步调用：{order_stk[i]}')

        # 随着多Agent的加入，需要将Agent的输出添加到用户问题中，作为参考信息
        cur_query = query
        print(f'Query is {cur_query}.\n')

        Agent_Message = ""
        # 依次运行Agent
        for i in range(len(order_stk)):
            cur_agent = agent_mapper[order_stk[i]]
            print(f'\n===============================\nStep: {i+1}: Currnet agent is {(cur_agent)}')
            print(f'\n-----> Current query is {cur_query}.')

            response = get_agent_response(cur_agent, cur_query)
            print(f'\n-----> Current response is {response}.\n')

            Agent_Message += f"*{order_stk[i]}*的回复为：{response}\n\n"
            # 如果当前Agent为最后一个Agent，则将其输出作为Multi Agent的输出
            if i == len(order_stk) - 1:
                prompt = f"请参考已知的信息：{Agent_Message}，回答用户的问题：{query}。"
                multi_agent_response = get_agent_response(summary_agent, prompt)
                print('*********************************      Multi-Agent回复为：     ****************************************\n')
                print(f'{multi_agent_response}\n')

                return multi_agent_response
            # 如果当前Agent不是最后一个Agent，则将上一个Agent的输出response添加到下一轮的query中，作为参考信息
            else:
                # 在参考信息前后加上特殊标识符，可以防止大模型混淆参考信息与提问
                # cur_query = f"你可以参考已知的信息：{response}你要完整地回答用户的问题。问题是：{query}。"
                cur_query = f"你可以参考已知的信息：{response} 问题是：{query}。"

            print('\n\n')
    # 兜底策略，如果上述程序运行失败，则直接调用大模型
    except Exception as e:
        print(e)
        # return get_agent_response(chat_agent,query)

if __name__ == '__main__':
    user_query = input("请输入您的问题：")

    # print(get_agent_response(planner_agent, user_query))
    get_multi_agent_response(user_query)

