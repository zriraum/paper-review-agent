

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



