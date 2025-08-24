

##Helper function: 
def get_relevant_messages(state: AgentState) -> List[AnyMessage]:
    '''
    Don't get tool call messages for AI from history.
    Get state from everything up to the most recent human message
    '''
    messages = state['messages']
    filtered_history = []
    for message in messages:
        if isinstance(message, HumanMessage) and message.content!="":
            filtered_history.append(message)
        elif isinstance(message, AIMessage) and message.content!="" and message.response_metadata['finish_reason']=="stop":
            filtered_history.append(message)
    last_human_index = state['last_human_index']
    return filtered_history[:-1] + messages[last_human_index:]

##1st node:
def process_input(state: AgentState):
    max_revision = 2
    messages = state.get('messages', [])

    last_human_index = len(messages) - 1
    for i in reversed(range(len(messages))):
        if isinstance(messages[i], HumanMessage):
            last_human_index = i
            break

    return {"last_human_index": last_human_index, "max_revisions" : max_revision, "revision_num" : 1}

def plan_node(state: AgentState):
    print("PLANNER")
    relevant_messages = get_relevant_messages(state)
    messages = [SystemMessage(content=planner_prompt)] + relevant_messages
    response = model.invoke(messages, temperature=temperature)
    print(response)
    print()
    return {"systematic_review_outline" : [response]}


def research_node(state: AgentState):
    print("RESEARCHER")
    review_plan = state['systematic_review_outline']
    messages = [SystemMessage(content=research_prompt)] + review_plan
    response = model.invoke(messages, temperature=temperature)
    print(response)
    print()
    return {"messages" : [response]}

def take_action(state: AgentState):
    ''' Get last message from agent state.
    If we get to this state, the language model wanted to use a tool.
    The tool calls attribute will be attached to message in the Agent State. Can be a list of tool calls.
    Find relevant tool and invoke it, passing in the arguments
    '''
    print("GET SEARCH RESULTS")
    last_message = state["messages"][-1]

    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {"messages": state['messages']}

    results = []
    for t in last_message.tool_calls:
        print(f'Calling: {t}')

        if not t['name'] in tools: # check for bad tool name
            print("\n ....bad tool name....")
            result = "bad tool name, retry" # instruct llm to retry if bad
        else:
            # pass in arguments for tool call
            result = tools[t['name']].invoke(t['args'])

        # append result as a tool message
        results.append(ToolMessage(tool_call_id = t['id'], name=t['name'], content=str(result)))

    return {"messages" : results} # langgraph adding to state in between iterations

def decision_node(state: AgentState):
    print("DECISION-MAKER")
    review_plan = state['systematic_review_outline']
    relevant_messages = get_relevant_messages(state)
    messages = [SystemMessage(content=decision_prompt)] + review_plan + relevant_messages
    response = model.invoke(messages, temperature=temperature)
    print(response)
    print()
    return {"messages" : [response]}

def article_download(state: AgentState):
    print("DOWNLOAD PAPERS")
    last_message = state["messages"][-1]

    try:
        # Handle different types of content
        if isinstance(last_message.content, str):
            urls = ast.literal_eval(last_message.content)
        else:
            urls = last_message.content

        filenames = []
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()

                # Create a papers directory if it doesn't exist
                if not os.path.exists('data'):
                    os.makedirs('data')

                # Generate a filename from the URL
                filename = f"data/{url.split('/')[-1]}"
                if not filename.endswith('.pdf'):
                    filename += '.pdf'

                # Save the PDF
                with open(filename, 'wb') as f:
                    f.write(response.content)

                filenames.append({"paper" : filename})
                print(f"Successfully downloaded: {filename}")

            except Exception as e:
                print(f"Error downloading {url}: {str(e)}")
                continue
        # Return AIMessage instead of raw strings
        return {
            "papers": [
                AIMessage(
                    content=filenames,
                    response_metadata={'finish_reason': 'stop'}
                )
            ]
        }
    except Exception as e:
        # Return error as AIMessage
        return {
            "messages": [
                AIMessage(
                    content=f"Error processing downloads: {str(e)}",
                    response_metadata={'finish_reason': 'error'}
                )
            ]
        }
