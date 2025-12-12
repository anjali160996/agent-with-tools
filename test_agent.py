"""
Test script to verify the agent and tool are working correctly.
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from http_tool import fetch_url_content

load_dotenv()

def test_tool_directly():
    """Test the tool directly to ensure it works."""
    print("Testing tool directly...")
    result = fetch_url_content.invoke({"url": "https://www.example.com"})
    print(f"Tool result: {result[:200]}...")
    print("✓ Tool works!\n")

def test_agent():
    """Test the agent with a simple query."""
    print("Testing agent...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Skipping agent test.")
        return
    
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    tools = [fetch_url_content]
    
    # Create agent - the framework automatically handles tool calling
    agent = create_agent(
        model=llm,
        tools=tools,
        debug=True
    )
    
    test_query = "What is the content of https://www.example.com?"
    print(f"Query: {test_query}\n")
    result = agent.invoke({"messages": [("user", test_query)]})
    
    # Extract the final message
    if "messages" in result and result["messages"]:
        final_message = result["messages"][-1]
        if hasattr(final_message, 'content'):
            print(f"\n✓ Agent result: {final_message.content[:200]}...")
        else:
            print(f"\n✓ Agent result: {str(final_message)[:200]}...")
    else:
        print(f"\n✓ Agent result: {str(result)[:200]}...")

if __name__ == "__main__":
    test_tool_directly()
    test_agent()

