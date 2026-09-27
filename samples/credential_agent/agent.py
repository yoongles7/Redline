from langchain.agents import AgentExecutor, create_react_agent
from tools.shell import run_shell
from tools.files import read_file, write_file
from tools.credentials import read_env_secret, upload_to_s3

tools = [run_shell, read_file, write_file, read_env_secret, upload_to_s3]

agent = create_react_agent(llm=None, tools=tools, prompt=None)
agent_executor = AgentExecutor(agent=agent, tools=tools)