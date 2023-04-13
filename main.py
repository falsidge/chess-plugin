import json

import quart
import quart_cors
from quart import request

import aiohttp
import chess

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
# Keep track of todo's. Does not persist if Python session is restarted.
_CHESS = {}
@app.post("/chess/board/<string:username>")
async def load_board(username):
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    _CHESS[username] = chess.Board(FEN)
    return quart.Response(response="OK", status=200)
@app.get("/chess/board/<string:username>")
async def get_board(username):
    board = _CHESS[username] = _CHESS.get(username, chess.Board())
    data = {"fen":board.fen()}
    return quart.Response(response=json.dumps(data), status=200)
@app.post("/chess/make_move/<string:username>")
async def make_move(username):
    request = await quart.request.get_json(force=True)

    move = request.get("move", "")
    print("move", move)
    try:
        board = _CHESS[username] = _CHESS.get(username, chess.Board())
        board.push_san(move)
    except ValueError:
        return quart.Response(response="Invalid move", status=400)
    data = {"fen":board.fen()}
    return quart.Response(response=json.dumps(data), status=200)
@app.get("/chess/valid_moves/<string:username>")
async def valid_moves(username):


    board = _CHESS[username] = _CHESS.get(username, chess.Board())

    data = {"moves":list(map(lambda x:x.uci(), board.generate_legal_moves()))}
    return quart.Response(response=json.dumps(data), status=200)
        
@app.get("/chess/analysis/<string:username>")
async def get_analysis(username):
    request = await quart.request.get_json(force=True)
    board = _CHESS[username] = _CHESS.get(username, chess.Board())
    async with aiohttp.ClientSession() as session:
        async with session.get('https://lichess.org/api/cloud-eval',params={"fen":board.fen()}) as response:
            data = await response.json()
            return quart.Response(response=json.dumps(data), status=200)
        
@app.post("/chess/analysis")
async def post_analysis():
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    async with aiohttp.ClientSession() as session:
        async with session.get('https://lichess.org/api/cloud-eval',params={"fen":FEN}) as response:
            data = await response.json()
            return quart.Response(response=json.dumps(data), status=200)

@app.post("/chess/display")
async def post_display():
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    chessboard = chess.Board(FEN)
    data = {"display":chessboard.unicode()}
    return quart.Response(response=json.dumps(data), status=200)
@app.get("/chess/display/<string:username>")
async def get_display(username):
    request = await quart.request.get_json(force=True)
    board = _CHESS[username] = _CHESS.get(username, chess.Board())

    data = {"display":board.unicode()}
    return quart.Response(response=json.dumps(data), status=200)

@app.get("/chess.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5003)

if __name__ == "__main__":
    main()
