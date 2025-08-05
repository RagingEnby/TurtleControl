import fastapi
import asyncio
import uuid
import json
from typing import Any, Literal, TypedDict


InteractableDirection = Literal["front", "up", "down"]
INSPECTABLE_DIRECTIONS: list[InteractableDirection] = ["front", "up", "down"]

MoveableDirection = Literal["forward", "back", "up", "down"]
InvSlot = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]


class Item(TypedDict):
    name: str
    count: int


class MCTurtle:
    def __init__(self, id: int, ws: fastapi.WebSocket):
        self.id = id
        self.ws = ws
        self.pending_requests: dict[str, asyncio.Future] = {}
        self._send_lock = asyncio.Semaphore(1)
        
    async def send_one_way(self, data: dict):
        await self.ws.send_json(data)
        
    async def msg(self, message: str):
        await self.send_one_way({
            "method": "msg",
            "content": message
        })
        
    async def send(self, data: dict, timeout: float = 30.0) -> dict | None:
        async with self._send_lock:
            nonce = str(uuid.uuid4())
            data["nonce"] = nonce
            
            future = asyncio.Future()
            self.pending_requests[nonce] = future
            
            try:
                await self.ws.send_json(data)
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                return None
            finally:
                self.pending_requests.pop(nonce, None)
            
    async def eval(self, code: str) -> Any:
        response = await self.send({
            "method": "eval",
            "content": code
        })
        if response:
            return response.get('content')
        else:
            print(f"Turtle #{self.id} eval timeout")
            return None
                        
    async def on_message(self, data: dict):
        nonce = data.get("nonce")
        if nonce and nonce in self.pending_requests:
            future = self.pending_requests[nonce]
            if not future.done():
                future.set_result(data)
            return
            
        if data.get("method") == "msg":
            print(f"Turtle #{self.id}: {data.get('content')}")
            
    async def loop(self):
        try:
            while True:
                msg = await self.ws.receive_json()
                asyncio.create_task(self.on_message(msg))
        except Exception as e:
            print(f"Turtle #{self.id} disconnected: {e}")
        finally:
            print(f"Turtle #{self.id} loop ended")
            
    """
    Turtle inspection API
    """
    async def get_blocks(self) -> dict[InteractableDirection, Item | None]:
        raw = await self.eval("return inspect()")
        return {d: raw.get(d) for d in INSPECTABLE_DIRECTIONS}
    
    async def inspect(self, direction: InteractableDirection | None = None) -> Item | None:
        blocks = await self.get_blocks()
        return blocks.get(direction or "front")
    
    inspect_up = lambda self: self.inspect("up")
    inspect_down = lambda self: self.inspect("down")
    
    """
    Turtle movement API
    """
    async def move(self, direction: MoveableDirection | None = None, distance: int | None = None):
        direction = direction or "forward"
        distance = distance or 1
        code = f"local s=0 for i=1,{distance} do if turtle.{direction}() then s=s+1 else break end end return s"
        successes = await self.eval(code)
        if successes < distance:
            block = await self.inspect(direction.replace("forward", "front")) if direction != "back" else None  # type: ignore[literal-required]
            if block:
                raise Exception(f"Block in the way: {block}")
            raise Exception(f"Only able to move {successes}/{distance} blocks")
    
    forward = lambda self, distance=None: self.move("forward", distance)
    back = lambda self, distance=None: self.move("back", distance)
    up = lambda self, distance=None: self.move("up", distance)
    down = lambda self, distance=None: self.move("down", distance)
    
    """
    Turtle dig API
    """
    async def dig(self, direction: InteractableDirection | None = None):
        direction = direction or "front"
        code = "turtle.dig{}()".format(direction.title() if direction != "front" else "")
        return await self.eval(code)
    
    dig_up = lambda self: self.dig("up")
    dig_down = lambda self: self.dig("down")
    
    """
    Turtle inventory API
    """
    async def get_inventory(self) -> dict[InvSlot, str | None]:
        inv = await self.eval("return inventory()")
        print('INVENTORY:', json.dumps(inv, indent=2))
        return {i: inv.get(str(i), None) for i in range(1, 17)}  # type: ignore[literal-required]
    
    async def get_slot(self, slot: InvSlot) -> str | None:
        inv = await self.get_inventory()
        return inv[slot]
    
    async def select(self, slot: InvSlot):
        return await self.eval(f"turtle.select({slot})")
    
    async def select_item(self, target: str):
        target = target.lower()
        inv = await self.get_inventory()
        for slot, item in inv.items():
            name = item['name'].lower() if item else None  # type: ignore[literal-required]
            if name and (target == name or name.replace('minecraft:', '') == target):
                return await self.select(slot)
        raise Exception(f"Item {target} not found in inventory")
    