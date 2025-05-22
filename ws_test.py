import websocket

def on_message(ws, message):
    print("<<<", message)

def on_error(ws, error):
    print("ERROR:", error)

def on_close(ws):
    print("CLOSED")

def on_open(ws):
    print("Connected!")

ws = websocket.WebSocketApp(
    "ws://localhost:8000/ws/posts/",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

ws.run_forever()
