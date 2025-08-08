from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
model = ChatOpenAI(
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    base_url="https://api.together.xyz/v1",
    temperature=0,
    api_key=os.getenv('TOGETHER_API_KEY')
)

server_params = StdioServerParameters(
    command="npx",
    env={
        "FIRECRAWL_API_KEY": os.getenv('FIRECRAWL_API_KEY')
    },
    args=["firecrawl-mcp"]
)

async def main():
    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            ## create the agent
            agent = create_react_agent(model,tools)

            messages = [
                {
                    "role":"system",
                    "content":"You are helpful assistant that can script websites, crawl pages and extract data using Firecrawl tools, think step by step and use the appropriate tools to help the user."
                }
            ]

            print("Availables tools - ",*[tool.name for tool in tools])
            print('-'*100)
            while True:
                user_input=input("\n You: ")
                if user_input == "quit" or user_input == "exit" or user_input =="q":
                    print('OK Bye.')
                    break
                messages.append({"role":"user", "content":user_input[:10000]}) # make sure the input is not so long
                try:
                    ## allow the agent to use all the tools from the firewrawl mcp server
                    agent_reponse = await agent.ainvoke({"messages":messages})

                    ai_message = agent_reponse["messages"][-1].content
                    print("\n Agent : ",ai_message)
                except Exception as e:
                    print('$'*100)
                    print(e)

if __name__ == "__main__":
    asyncio.run(main())