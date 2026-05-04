from fastapi import FastAPI #import
import uuid
from app.models.state import DebateState
from app.models.debate import DebateRequest
from openai import OpenAI
from fastapi import HTTPException
import requests

client = OpenAI()

app = FastAPI() # starting the fastapi server 

debates = {} #dict to store - local memory

@app.post("/start-debate")
def start_debate(request : DebateRequest):
    debate_id = str(uuid.uuid4())
    print(debates)

    state = DebateState(   #creating an obj for debatestate
        debate_id=debate_id,
        topic=request.topic,
        context=request.context,
        rounds=[],
        status="in_progress"
    )

    debates[debate_id] = state

    return {"debate_id": debate_id}  #handle to access that debate, debate id is the key and state is the value 

# we use debate id because there might be 2 open status debates going on, so when the user says to start the debate, the system should be able to know which one 

@app.get("/debate/{debate_id}")
def get_debate(debate_id: str):
    if debate_id not in debates:
        return {"error":"not found"}
    
    return debates[debate_id]

@app.post("/next-round")
def next_round(debate_id: str):
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")

    state = debates[debate_id]

    A_response = generate_agent_response(
    role="pro",
    topic=state.topic,
    context=state.context,
    history=state.rounds
)

    B_response = generate_agent_response(
    role="con",
    topic=state.topic,
    context=state.context,
    history=state.rounds + [{"A": A_response}] # B now sees what A said 
)

    round_data = {
        "round": "opening",
        "A": A_response,
        "B": B_response
    }


    state.rounds.append(round_data)

    debates[debate_id] = state

    return state


def generate_agent_response(role: str, topic: str, context: str | None, history):

    if role == "pro":
        stance = "You strongly support this topic."
    else:
        stance = "You strongly oppose the topic."

    prompt = f"{stance} Topic: {topic}. "

    if context:
        prompt += f"Context: {context}. "

    if history and len(history) > 0:
        last = history[-1]
        opponent = last.get("B") if role == "pro" else last.get("A")

        if opponent:
            prompt += f"Your opponent said: '{opponent}'. Respond to it. "

    if role == "pro":
        prompt += "Argue why the topic is beneficial."
    else:
        prompt += "Argue why the topic is problematic."

    response = requests.post(                               #using local ollama model 
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]



@app.get('/')
def default_message():
    return {"message":"server is running"}


