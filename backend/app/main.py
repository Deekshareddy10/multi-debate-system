from fastapi import FastAPI #import
import uuid
from app.models.state import DebateState
from app.models.debate import DebateRequest

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

    A_response = generate_agent_response("pro", state.topic, state.context)
    B_response = generate_agent_response("con", state.topic, state.context)
    round_data = {
        "round": "opening",
        "A": A_response,
        "B": B_response
    }


    state.rounds.append(round_data)

    debates[debate_id] = state

    return state

def generate_agent_response(role: str, topic: str, context: str | None):

    base = f"The topic is: {topic}."

    if context:
        base += f" Additional context: {context}."

    if role == "pro":
        return base + " I support this topic because it provides clear advantages."
    else:
        return base + " I oppose this topic because it raises serious concerns."
    

@app.get('/')
def default_message():
    return {"message":"server is running"}


