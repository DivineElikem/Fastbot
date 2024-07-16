from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, AnyMessage
from typing import List, Union
from dotenv import dotenv_values

HUGGINGFACE_API_TOKEN = dotenv_values(".env")

os.environ["HUGGINGFACE_API_TOKEN"] = HUGGINGFACE_API_TOKEN

llm = HuggingFaceEndpoint(repo_id="mistralai/Mistral-7B-Instruct-v0.3", max_new_tokens=2000)

chatmodel = ChatHuggingFace(llm=llm)

async def call_chatmodel(user_message: str, chat_history: List[AnyMessage] = []):
    messages = [SystemMessage(content="You are helpful assistant")]
    messages += chat_history
    messages.append(HumanMessage(content=f"{user_message}"))
    
    response = chatmodel.invoke([HumanMessage(content=f"{messages}")])
    messages.append(AIMessage(content=response.content))
    return {"response": response.content, "messages": messages}

