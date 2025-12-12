# LangChain Agent with Custom HTTP Tool

This project demonstrates a LangChain-based agent that automatically uses a custom HTTP tool to fetch and answer questions about URL content.

## Features

- **ReAct Agent**: Uses LangChain's ReAct agent framework that automatically decides when to use tools
- **Custom HTTP Tool**: A custom tool that fetches content from URLs
- **Automatic Tool Calling**: The agent internally calls tools without just listing them - it actually executes them

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your OpenAI API key:**
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your-api-key-here
     ```

## Usage

Run the agent:
```bash
python agent.py
```

Then enter queries like:
- "What is the content of https://example.com?"
- "Fetch and summarize the content from https://www.python.org"
- "Tell me about the content at https://news.ycombinator.com"

The agent will automatically:
1. Recognize that your query involves a URL
2. Call the `fetch_url_content` tool internally
3. Process the fetched content
4. Return a response based on the content

## How It Works

The project uses LangChain's **ReAct agent** pattern:
- The agent receives your query
- It reasons about what tools it needs to use
- It automatically calls the `fetch_url_content` tool when it detects a URL in your query
- It processes the tool's response and provides a final answer

The key difference from other approaches is that the agent **executes** the tools internally rather than just suggesting which tools could be used.

## Project Structure

- `agent.py`: Main agent script with ReAct agent setup
- `http_tool.py`: Custom HTTP tool for fetching URL content
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment variable file

## Testing

Run the test script to verify everything is working:
```bash
python test_agent.py
```

This will:
1. Test the HTTP tool directly
2. Test the agent with a sample query

## Troubleshooting

If tools are not being called:
1. Make sure `verbose=True` in `AgentExecutor` to see the agent's reasoning
2. Check that your query clearly mentions a URL
3. Ensure your OpenAI API key is correctly set in `.env`
4. Verify that the LangChain Hub prompt is accessible (it should pull automatically)
5. Run `test_agent.py` to verify the tool works independently
6. Check the verbose output - you should see "Action:" and "Action Input:" when the tool is called

## Key Points

- The agent uses **ReAct pattern** which means it will:
  - **Think** about what to do
  - **Act** by calling a tool
  - **Observe** the tool's result
  - **Think** again and provide a final answer

- The tool is called **automatically** when the agent determines it needs URL content
- You don't need to explicitly tell the agent to use the tool - it decides based on your query

