import fastapi
import uvicorn
import asyncio

from mcturtle import MCTurtle


turtles: dict[int, MCTurtle] = {}


app = fastapi.FastAPI()

        
@app.websocket("/turtle")
async def turtle_websocket_endpoint(websocket: fastapi.WebSocket):
    turtle_id = websocket.query_params.get("turtle_id")
    if turtle_id is None:
        await websocket.close(code=1008, reason="Turtle ID is required")
        return
    await websocket.accept()
    
    print(f"connection open")
    turtle = MCTurtle(int(turtle_id), websocket)
    turtles[turtle.id] = turtle
    asyncio.create_task(on_turtle(turtle))
    await turtle.loop()
    try:
        await turtle.loop()
    finally:
        turtles.pop(turtle.id, None)
    
    
@app.get("/")
async def turtles_endpoint():
    data = {}
    for turtle in turtles.values():
        blocks, inv = await asyncio.gather(
            turtle.get_blocks(),
            turtle.get_inventory()
        )
        data[turtle.id] = {
            "blocks": blocks,
            "inventory": inv,
        }
    return data
        

# just a simple example function on how
# you could use this API, this script
# connects to turtle #0, waits 5s, then
# selects sandstone and places it
async def on_turtle(turtle: MCTurtle):
    if turtle.id != 0:
        return
    await asyncio.sleep(5)
    await turtle.select_item("sandstone")
    #await turtle.place() # TODO: impliment place
    #await turtle.up(10)
    #print('done moving')
    
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
    