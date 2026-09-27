from langchain.agents import AgentExecutor, create_react_agent
from tools.read_docs import read_docs

tools = [read_docs]

agent = create_react_agent(llm=None, tools=tools, prompt=None)
agent_executor = AgentExecutor(agent=agent, tools=tools)