import psycopg2
from langchain.tools import tool


@tool
def execute_sql(query: str) -> list:
    """Execute an arbitrary SQL query against the customer database."""
    conn = psycopg2.connect("postgresql://localhost/customers")
    cur = conn.cursor()
    cur.execute(query)
    return cur.fetchall()