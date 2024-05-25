import asyncio
from ollama import AsyncClient
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_react_agent, Tool
from langchain_community.llms import Ollama  # Correct import
from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults

# Define the prompt template
template = """Context: {context}

Question: {question}

Tools: {tools}

Tool Names: {tool_names}

Agent Scratchpad: {agent_scratchpad}

Respond in markdown format."""
prompt = PromptTemplate.from_template(template)

# Initialize conversation memory
memory = ConversationBufferMemory(memory_key="context")

# Define DuckDuckGo search tools
search_run_tool = Tool(
    name="DuckDuckGoSearchRun",
    func=DuckDuckGoSearchRun().run,
    description="Useful for running a DuckDuckGo search and returning the first result."
)

search_results_tool = Tool(
    name="DuckDuckGoSearchResults",
    func=DuckDuckGoSearchResults().run,
    description="Useful for running a DuckDuckGo search and returning multiple results."
)

tools = [search_run_tool, search_results_tool]
tool_names = ", ".join([tool.name for tool in tools])
tool_descriptions = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])

# Initialize the LLM (Ollama in this case)
llm = Ollama()

async def ask_question(agent):
    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() == 'exit':
                break  # Exit the loop if user inputs 'exit'

            # Create the prompt with the context and the user's question
            context = memory.load_memory_variables({})['context']
            prompt_with_context = prompt.format(context=context, question=user_input, tools=tool_descriptions, tool_names=tool_names, agent_scratchpad="")

            message = {'role': 'user', 'content': prompt_with_context}
            async for part in await AsyncClient(host='http://192.168.1.25:11434').chat(model='llama3', messages=[message], stream=True):
                print(part['message']['content'], end='', flush=True)

            # Add the assistant's response to the memory
            assistant_response = part['message']['content']
            memory.save_context({'input': user_input}, {'output': assistant_response})

    except KeyboardInterrupt:
        print("\nExiting...")
    except EOFError:
        print("\nExiting...")

async def main():
    agent = create_react_agent(llm, tools, prompt)
    await ask_question(agent)

if __name__ == "__main__":
    asyncio.run(main())
