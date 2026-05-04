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
def get_debate(debate_id:str):
    if debate_id not in debates:
        return {"error":"not found"}
    
    return debates[debate_id]


@app.get('/')
def default_message():
    return {"message":"server is running"}


