from typing import Any, List, TypedDict, Annotated, Dict
import operator
from uuid import uuid4
from langchain_core.messages import AnyMessage

def reduce_messages(left: list[AnyMessage], right: list[AnyMessage]) -> list[AnyMessage]:
    # assign ids to messages that don't have them
    for message in right:
        if not message.id:
            message.id = str(uuid4())
    # merge the new messages with the existing messages
    merged = left.copy()
    for message in right:
        for i, existing in enumerate(merged):
            # replace any existing messages with the same id
            if existing.id == message.id:
                merged[i] = message
                break
        else:
            # append any new messages to the end
            merged.append(message)
    return merged

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], reduce_messages]
    systematic_review_outline : str
    last_human_index : int
    papers : Annotated[List[str], operator.add] ## papers downloaded
    analyses: Annotated[List[Dict], operator.add]  # Store analysis results
    combined_analysis: str  # Final combined analysis

    title: str
    abstract : str
    introduction : str
    methods : str
    results : str
    conclusion : str
    references : str

    draft : str
    revision_num : int
    max_revisions : int