import json
import os
import shutil
import uuid
from typing import Dict

import pika
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import JSONResponse, HTMLResponse


class PDFCreator:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        self.channel = self.connection.channel()

        self.channel.queue_declare(queue="pdf_queue")
        self.callback_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )
        self.response = b''
        self.corr_id = ''
        self.ID = 0
        self.CAPTIONS = {}

    def on_response(self, ch, method, props, body: bytes) -> None:
        if self.corr_id == props.correlation_id:
            self.response = body

    def main_call(self, req: str) -> None:
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='PDF_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=req.encode())


class Player:
    d_name: str
    d_sex: str
    d_e_mail: str
    d_avatar: bytes
    d_avatar_name: str
    d_session: int
    d_wins: int
    d_losses: int
    d_time: float

    def __init__(self, name: str):
        self.d_name = name
        self.d_sex = ""
        self.d_avatar = b""
        self.d_e_mail = ""
        self.d_session = 0
        self.d_wins = 0
        self.d_losses = 0
        self.d_time = 0

    def set_sex(self, sex: str):
        self.d_sex = sex

    def set_email(self, e_mail: str):
        self.d_e_mail = e_mail

    async def set_avatar(self, avatar: File):
        self.d_avatar = await avatar.read()
        self.d_avatar_name = avatar.filename

    def add_session(self):
        self.d_session += 1

    def add_win(self):
        self.d_wins += 1

    def add_lose(self):
        self.d_losses += 1

    def add_time(self, time):
        self.d_time += time


app = FastAPI()
players: Dict[str, Player] = {}


# service = PDFCreator()


@app.put("/nickname/{nick}")
async def set_nickname(nick: str):
    if nick not in players.keys():
        try:
            os.mkdir(f"{nick}")
        except FileExistsError:
            shutil.rmtree(f"{nick}")
            os.mkdir(f"{nick}")
        players[nick] = Player(nick)
        return f"Your player is registered with nick {nick}"
    else:
        return "Nick is occupied, choose another"


@app.post("/avatar/{nick}")
async def set_avatar(nick: str, file: UploadFile = File(...)):
    if nick in players.keys():
        await players[nick].set_avatar(file)
        with open(f"{nick}/{nick}.png", 'wb') as f:
            f.write(players[nick].d_avatar)
        return f"{nick} avatar is set."
    else:
        return "Nick is occupied, choose another"


@app.put("/sex/{nick}/{sex}")
async def set_sex(nick: str, sex: str):
    if nick in players.keys():
        players[nick].set_sex(sex)
        return f"{nick} sex is set to {sex}"
    else:
        return f"No such player with nick {nick}"


@app.put("/email/{nick}/{e_mail}")
async def set_email(nick: str, e_mail: str):
    if nick in players.keys():
        players[nick].set_email(e_mail)
        return f"{nick} e_mail is set to {e_mail}"
    else:
        return f"No such player with nick {nick}"


@app.get("/player/{nick}")
async def get_player(nick: str):
    if nick.count(',') != 0:
        d: Dict[str, JSONResponse] = dict()
        for nick in nick.split(', '):
            d[nick] = await get_player(nick)
        return d
    if nick in players.keys():
        with open(f"{nick}/{nick}.json", "w") as file:
            json.dump({
                "Nick": nick,
                "Avatar": players[nick].d_avatar_name,
                "Sex": players[nick].d_sex,
                "E-mail": players[nick].d_e_mail,
                "Games": players[nick].d_session,
                "Wins": players[nick].d_wins,
                "Losses": players[nick].d_losses,
                "Time": players[nick].d_time
            }, file)
        return JSONResponse({
            "Nick": nick,
            "Avatar": players[nick].d_avatar_name,
            "Sex": players[nick].d_sex,
            "E-mail": players[nick].d_e_mail,
            "Games": players[nick].d_session,
            "Wins": players[nick].d_wins,
            "Losses": players[nick].d_losses,
            "Time": players[nick].d_time
        })
    else:
        return f"No such player with a nick {nick}"


@app.put("/{nick}/new_session")
def add_session(nick: str):
    if nick in players.keys():
        players[nick].add_session()
        return f"New session add to {nick} counter"
    else:
        return f"No such player with nick {nick}"


@app.put("/{nick}/new_win")
def add_win(nick: str):
    if nick in players.keys():
        players[nick].add_win()
        return f"New win add to {nick} counter"
    else:
        return f"No such player with nick {nick}"


@app.put("/{nick}/new_lose")
def add_lose(nick: str):
    if nick in players.keys():
        players[nick].add_lose()
        return f"New win add to {nick} counter"
    else:
        return f"No such player with nick {nick}"


@app.put("/{nick}/new_time/{time}")
def add_lose(nick: str, time: float):
    if nick in players.keys():
        players[nick].add_time(time)
        return f"{time} add to {nick} counter"
    else:
        return f"No such player with nick {nick}"


@app.get("/{nick}/create_pdf")
def get_pdf(nick: str, request: Request):
    try:
        with open(f"{nick}/{nick}.json", 'r') as file:
            data = json.load(file)
    except:
        data = {'Nick': nick,
                'Sex': players[nick].d_sex,
                'E-mail': players[nick].d_e_mail,
                'Games': players[nick].d_session,
                'Wins': players[nick].d_wins,
                'Losses': players[nick].d_losses,
                'Time': players[nick].d_time}

    markdown_body = f"# {data['Nick']}\n" \
                    f"![player avatar]({nick}/{nick}.png)\\\n" \
                    f"Sex: {data['Sex']}\\\n" \
                    f"E-mail: {data['E-mail']}\\\n" \
                    f"Games: {data['Games']}\\\n" \
                    f"Wins: {data['Wins']}\\\n" \
                    f"Losses: {data['Losses']}\\\n" \
                    f"Time: {data['Time']}\\\n"
    with open(f"{nick}/{nick}.md", 'w') as file:
        file.write(markdown_body)
    os.system(f"pandoc {nick}/{nick}.md -o {nick}/{nick}.pdf")
    return f"{request.base_url}{nick}.pdf"


@app.get("/{nick}.pdf", response_class=HTMLResponse)
def show_pdf(nick: str):
    return f"""
    <html>
        <head>
        </head>
        <body>
            <embed src="{nick}/{nick}.pdf" width="800px" height="2100px" />
        </body>
    </html>
    """
