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
    round_number = len(state.rounds)+1
    if round_number == 1:
        round_type = "opening"
    elif round_number == 2:
        round_type = "rebuttal"
    elif round_number == 3:
        round_type = "counter"
    else:
        round_type = "closing"

    if len(state.rounds) >= 4:
        return {"message": "Debate already completed"}

    A_response = generate_agent_response(
    role="pro",
    topic=state.topic,
    context=state.context,
    history=state.rounds,
    round_type = round_type
)

    B_response = generate_agent_response(
    role="con",
    topic=state.topic,
    context=state.context,
    history=state.rounds + [{"A": A_response}], # B now sees what A said 
    round_type = round_type
)

    round_data = {
        "round": round_type,
        "A": A_response,
        "B": B_response
    }


    state.rounds.append(round_data)

    debates[debate_id] = state

    return state


def generate_agent_response(role: str, topic: str, context: str | None, history, round_type):

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

    if round_type == "opening":
        prompt += "Give your main argument clearly."

    elif round_type == "rebuttal":
        prompt += "Directly challenge your opponent’s argument."

    elif round_type == "counter":
        prompt += "Strengthen your position and counter weaknesses."

    elif round_type == "closing":
        prompt += "Summarize your position and conclude strongly."

def judge_debate(state):
    prompt = f"""
You are an unbiased debate judge.

Debate Topic: {state.topic}

Debate Rounds:
"""

    for r in state.rounds:
        prompt += f"\nRound: {r['round']}\n"
        prompt += f"A (Pro): {r['A']}\n"
        prompt += f"B (Con): {r['B']}\n"

    prompt += """
Analyze the arguments carefully.

Decide:
1. Who presented stronger arguments (A or B)
2. Why
3. Give a short explanation

Return in format:
Winner: A or B
Reason: ...
"""    

    response = requests.post(                               #using local ollama model 
        "http://localhost:11434/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
    )

    return response.json()["response"]

@app.get("/judge/{debate_id}")
def judge(debate_id: str):
    if debate_id not in debates:
        raise HTTPException(status_code=404, detail="Debate not found")

    state = debates[debate_id]
    result = judge_debate(state)
    
    
    winner, reason = parse_judgement(result)

    return {
        "debate_id": debate_id,
        "result": result
    }

def parse_judgement(result): #helper function to understand the responses better 
    lines = result.split("\n")
    winner = None
    reason = ""

    for line in lines:
        if "Winner" in line:
            winner = line.split(":")[-1].strip()
        if "Reason" in line:
            reason = line.split(":")[-1].strip()

    return winner, reason

@app.get('/')
def default_message():
    return {"message":"server is running"}


