import discord
from discord import app_commands
import sys
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return " "

def run_flask():
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

class TestBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("[+] Comandos sincronizados globalmente.")

    async def on_ready(self):
        print(f"[+] Bot conectado como {self.user} (ID: {self.user.id})")
        print(f"[+] Servidores: {len(self.guilds)}")

client = TestBot()

@client.tree.command(name="test", description="Responde con 'Test Msg'")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("Test Msg", ephemeral=False)

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
