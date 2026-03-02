# Avancement_bot.py
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Charger le token et le guild_id depuis les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # ID du serveur Discord

# Intents nécessaires (pour les rôles et membres)
intents = discord.Intents.default()
intents.members = True  # Privileged intent
intents.guilds = True

# Création du bot
client = commands.Bot(command_prefix="!", intents=intents)

# --- EVENTS ---
@client.event
async def on_ready():
    # Synchronisation des commandes slash sur le serveur
    guild = discord.Object(id=GUILD_ID)
    await client.tree.sync(guild=guild)
    print(f"Bot prêt. Connecté comme {client.user}")

# --- COMMANDES SLASH ---
@client.tree.command(name="role", description="Attribuer un rôle à un membre")
@discord.app_commands.describe(member="Membre à qui attribuer le rôle", role="Rôle à attribuer")
async def role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f"{member.mention} a reçu le rôle {role.name}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Erreur : {str(e)}", ephemeral=True)

# --- LANCEMENT ---
client.run(TOKEN)
