local ws;


function _G.inspect()
    local upBlock, upData = turtle.inspectUp()
    local frontBlock, frontData = turtle.inspect()
    local downBlock, downData = turtle.inspectDown()
    return {
        up = (upBlock and upData.name) or nil,
        front = (frontBlock and frontData.name) or nil,
        down = (downBlock and downData.name) or nil,
    }
end


function _G.inventory()
    local inv = {}
    for i = 1, 16 do
        local item = turtle.getItemDetail(i)
        if item then
            inv[tostring(i)] = {
                name = item.name,
                count = item.count,
            }
        end
    end
    print(textutils.serialiseJSON(inv))
    return inv
end


function eval(code)
    print('EVAL: ' .. code)
    local func = load(code)
    local result = func()
    return result
end


function send(data)
    ws.send(textutils.serialiseJSON(data))
end


function onWsMessage(data)
    if data.method == "msg" then
        print('FROM SERVER: ' .. data.content)
    elseif data.method == "eval" then
        local result = eval(data.content)
        send({
            method = "eval",
            content = result,
            nonce = data.nonce
        })
    end
end


function wsLoop()
    local backoff = 1
    while true do
        print('Attempting to connect...')
        ws = http.websocket("ws://localhost:8080/turtle?turtle_id=" .. os.getComputerID())
        if ws then
            print('Connected to server')
            backoff = 1
            local success, err = pcall(function()
                while true do
                    local msg = ws.receive()
                    if msg then
                        print('received: ' .. msg)
                        onWsMessage(textutils.unserialiseJSON(msg))
                    else
                        error("Connection lost")
                    end
                end
            end)
            print('Disconnected: ' .. tostring(err))
            ws.close()
        else
            print('Failed to connect')
        end
        print('Retrying in ' .. backoff .. ' seconds...')
        sleep(backoff)
        backoff = math.min(backoff * 2, 10)
    end
end


wsLoop()
