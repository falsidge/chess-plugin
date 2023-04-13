import urllib.parse
import json

import quart
import quart_cors
from quart import request

import aiohttp
import chess
import chess.svg

import cairosvg

app = quart_cors.cors(quart.Quart(__name__),
                      allow_origin="https://chat.openai.com")
_CHESS = {}


@app.post("/chess/board/<string:username>")
async def load_board(username):
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    if FEN == "":
        _CHESS[username] = chess.Board()
    else:
        _CHESS[username] = chess.Board(FEN)
    return quart.Response(response="OK", status=200)


@app.get("/chess/board/<string:username>")
async def get_board(username):
    board = _CHESS[username] = _CHESS.get(username, chess.Board())
    data = {"fen": board.fen()}
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
    data = {"fen": board.fen()}
    return quart.Response(response=json.dumps(data), status=200)


@app.get("/chess/valid_moves/<string:username>")
async def valid_moves(username):

    board = _CHESS[username] = _CHESS.get(username, chess.Board())

    data = {"moves": list(
        map(lambda x: x.uci(), board.generate_legal_moves()))}
    return quart.Response(response=json.dumps(data), status=200)


@app.get("/chess/analysis/<string:username>")
async def get_analysis(username):
    board = _CHESS[username] = _CHESS.get(username, chess.Board())
    async with aiohttp.ClientSession() as session:
        async with session.get('https://lichess.org/api/cloud-eval', params={"fen": board.fen()}) as response:
            data = await response.json()
            return quart.Response(response=json.dumps(data), status=200)


@app.post("/chess/analysis")
async def post_analysis():
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    async with aiohttp.ClientSession() as session:
        async with session.get('https://lichess.org/api/cloud-eval', params={"fen": FEN}) as response:
            data = await response.json()
            return quart.Response(response=json.dumps(data), status=200)


@app.post("/chess/display")
async def post_display():
    request = await quart.request.get_json(force=True)
    FEN = request.get("fen", "")
    print(FEN)
    chessboard = chess.Board(FEN)
    url = app.url_for(
        'get_png_fen', fen=urllib.parse.quote_plus(FEN),  _external=True)

    data = {"display": {
        "png": f"[Chessboard]({url}", "ascii": chessboard.unicode(), }}
    return quart.Response(response=json.dumps(data), status=200)


@app.get("/chess/display/<string:username>")
async def get_display(username):
    chessboard = _CHESS[username] = _CHESS.get(username, chess.Board())

    url = app.url_for('get_png_fen', fen=urllib.parse.quote_plus(
        chessboard.fen()),  _external=True)
    data = {"display": {
        "png": f"[Chessboard]({url})", "ascii": chessboard.unicode(), }}

    return quart.Response(response=json.dumps(data), status=200)


@app.get("/chess/svg/<string:username>.svg")
async def get_svg(username):
    chessboard = _CHESS[username] = _CHESS.get(username, chess.Board())

    return quart.Response(response=chess.svg.board(chessboard), status=200, mimetype="img/svg+xml")


@app.get("/chess/png/<string:username>.png")
async def get_png(username):
    chessboard = _CHESS[username] = _CHESS.get(username, chess.Board())

    return quart.Response(response=cairosvg.svg2png(chess.svg.board(chessboard)), status=200, mimetype="img/svg+xml")


@app.get("/chess/png/fen/<string:fen>.png")
async def get_png_fen(fen):
    chessboard = chess.Board(urllib.parse.unquote_plus(fen))

    return quart.Response(response=cairosvg.svg2png(chess.svg.board(chessboard)), status=200, mimetype="img/svg+xml")


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
