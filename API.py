from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List
from Instance import agv_num

from starlette.websockets import WebSocketState

from GA import GA
from Instance import Generate

app = FastAPI()
# 用于存储所有 WebSocket 连接的列表
websockets: List[WebSocket] = []
class TypeModel(BaseModel):
    job:int
    machine:List[int]
    state:int
    processtime:List[List[List[int]]]

class ReturnTypeModel(BaseModel):
    job:int
    machine:List[int]
    state:int
    scheduleresult:List[List[int]]


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data_json = TypeModel.parse_raw(data)
            await websocket.send_text(f"Received type: {data_json.type}")
    except WebSocketDisconnect:
        print("Client disconnected")





@app.post("/receive-type")
async def receive_type(input_data: TypeModel):
    # 这里你可以处理接收到的数据
    if len(input_data.processtime)!=input_data.state:
        return {"ok":False,"message":"input data error"}
    for i,x in enumerate(input_data.processtime):
        if len(x)!=input_data.machine[i]:
            return {"ok":False,"message":"input data error"}
        for j,y in enumerate(x):
            if len(y)!=input_data.job:
                return {"ok":False,"message":"input data error"}

    PT,agv_trans=Generate(input_data.state,input_data.job,input_data.machine)
    g=GA(input_data.job,input_data.state,input_data.machine,PT,agv_trans,agv_num)
    result=g.mainagain()
    data={
        "ok":True,
        "job":input_data.job,
        "machine":input_data.machine,
        "state":input_data.state,
        "result":result
    }

    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.230.64", port=8000)






















