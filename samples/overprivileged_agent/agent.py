from langchain.agents import AgentExecutor, create_react_agent
from tools.customer_db import read_customer, update_customer
from tools.email import send_email
from tools.sql import execute_sql

tools = [read_customer, update_customer, send_email, execute_sql]

agent = create_react_agent(llm=None, tools=tools, prompt=None)
agent_executor = AgentExecutor(agent=agent, tools=tools)