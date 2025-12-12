"""
LangChain agent that automatically uses tools to answer questions about URL content.
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from http_tool import fetch_url_content

# Load environment variables
load_dotenv()

def create_agent_executor():
    """
    Creates an agent that automatically calls tools - the agent framework handles everything.
    """
    # Initialize the LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
    )
    
    # Define the tools available to the agent
    tools = [fetch_url_content]
    
    # Create agent - this automatically handles tool calling in a loop
    # The agent framework internally manages tool execution
    agent = create_agent(
        model=llm,
        tools=tools,
        debug=True  # Set to True to see agent's internal operations
    )
    
    return agent


def main():
    """
    Main function to run the agent interactively.
    """
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your-api-key-here")
        return
    
    # Create the agent
    print("Initializing agent...")
    agent = create_agent_executor()
    print("Agent ready! Type 'exit' to quit.\n")
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("\nEnter your query (or 'exit' to quit): ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Invoke the agent with the user's query
            # The agent framework automatically handles tool calling internally
            # No manual tool execution - everything is handled by the agent
            print("\nProcessing your query...\n")
            result = agent.invoke({"messages": [("user", user_input)]})
            
            # Display the result
            print("\n" + "="*50)
            print("RESPONSE:")
            print("="*50)
            # Extract the final message from the agent's response
            if "messages" in result and result["messages"]:
                final_message = result["messages"][-1]
                if hasattr(final_message, 'content'):
                    print(final_message.content)
                else:
                    print(str(final_message))
            else:
                print(str(result))
            print("="*50)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            traceback.print_exc()
            print("Please try again.")


if __name__ == "__main__":
    main()

