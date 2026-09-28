import discord
from discord import app_commands
import requests
import sys
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return " "

def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

def fetch_quote():
    try:
        response = requests.post(
            "https://api.vndb.org/kana/quote",
            headers={"Content-Type": "application/json"},
            json={
                "fields": "vn{id,title},character{id,name,image.url},quote",
                "filters": ["random", "=", 1]
            },
            timeout=15
        )
        if response.status_code != 200:
            return None
        data = response.json()
        results = data.get("results", [])
        if not results:
            return None
        return results[0]
    except Exception:
        return None

class QuoteBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("[+] Comandos sincronizados globalmente.")

    async def on_ready(self):
        print(f"[+] Bot conectado como {self.user} (ID: {self.user.id})")

client = QuoteBot()

@client.tree.command(name="quote", description="Muestra una cita aleatoria de una visual novel")
async def quote_command(interaction: discord.Interaction):
    await interaction.response.defer()

    result = fetch_quote()
    if not result:
        await interaction.followup.send("❌ No se pudo obtener una cita.")
        return

    quote_text = result.get("quote", "")
    vn = result.get("vn") or {}
    character = result.get("character")

    vn_id = vn.get("id", "")
    vn_title = vn.get("title", "")
    vn_url = f"https://vndb.org/{vn_id}" if vn_id else "https://vndb.org"
    vn_display = f"[{vn_title}]({vn_url})"

    if character:
        char_name = character.get("name", "")
        char_id = character.get("id", "")
        char_url = f"https://vndb.org/{char_id}" if char_id else "https://vndb.org"
        char_display = f"[{char_name}]({char_url})"
        char_image = (character.get("image") or {}).get("url")
        author_line = f"{vn_display} - {char_display}"
    else:
        char_image = None
        author_line = vn_display

    embed = discord.Embed(
        description=f"# __*{quote_text}*__\n\n— {author_line}",
        color=discord.Color.blurple()
    )

    file = None
    if char_image:
        try:
            img_response = requests.get(char_image, timeout=15)
            if img_response.status_code == 200:
                file = discord.File(fp=__import__("io").BytesIO(img_response.content), filename="character.jpg")
                embed.set_thumbnail(url="attachment://character.jpg")
        except Exception:
            pass

    if file:
        await interaction.followup.send(embed=embed, file=file)
    else:
        await interaction.followup.send(embed=embed)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python script.py <TOKEN>")
        sys.exit(1)

    TOKEN = sys.argv[1]

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("[+] Flask corriendo en el puerto 8080.")

    try:
        client.run(TOKEN)
    except discord.LoginFailure:
        print("[!] Token inválido.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Cerrando...")
