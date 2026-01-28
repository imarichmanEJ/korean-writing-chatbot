from core.memory import memory
from node.state import WritingState
from node.generation import generation_node
from node.evaluation import evaluation_node
from node.summarization import summarization_node
from node.qa import qa_node, tools
from node.supervisor import supervisor_node, route_supervisor
from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.graph import StateGraph, START, END

builder = StateGraph(WritingState)
builder.add_node('supervisor', supervisor_node)
builder.add_node('generation', generation_node)
builder.add_node('evaluation', evaluation_node)
builder.add_node('summarization', summarization_node)
builder.add_node('qa', qa_node)
builder.add_node('tools', ToolNode(tools))

builder.add_edge(START, 'supervisor')
builder.add_conditional_edges('supervisor',route_supervisor)
builder.add_edge('generation', END)
builder.add_edge('evaluation', END)
builder.add_edge('summarization', END)
builder.add_conditional_edges('qa', tools_condition)
builder.add_edge('tools', 'qa')
graph = builder.compile(checkpointer=memory)



