import discord
from discord.ext import commands
from discord import app_commands
import os

# --- Variables d'environnement ---
TOKEN = os.getenv("TOKEN_AVANCEMENT")  # Token bot sur Railway
GUILD_ID = int(os.getenv("GUILD_ID"))  # ID du serveur Discord

# --- Intents ---
intents = discord.Intents.default()
intents.members = True         # nécessaire pour assigner les rôles
intents.message_content = True # optionnel, si tu veux lire des messages

# --- Client et CommandTree ---
client = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(client)

# --- Commande /role ---
@tree.command(
    name="role",
    description="Assigner un rôle d'avancement à un membre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    role="Nom du rôle à assigner (Trad, Check, Clean, Edit)",
    membre="Membre concerné"
)
async def role(interaction: discord.Interaction, role: str, membre: discord.Member):
    guild = interaction.guild
    role_obj = discord.utils.get(guild.roles, name=role)
    if not role_obj:
        await interaction.response.send_message(f"Rôle '{role}' introuvable.", ephemeral=True)
        return
    
    await membre.add_roles(role_obj)
    await interaction.response.send_message(f"{membre.mention} a reçu le rôle '{role}'.", ephemeral=True)

# --- Commande /status ---
@tree.command(
    name="status",
    description="Voir qui a quel rôle d'avancement",
    guild=discord.Object(id=GUILD_ID)
)
async def status(interaction: discord.Interaction):
    guild = interaction.guild
    roles = ["Trad", "Check", "Clean", "Edit", "QEdit"]
    embed = discord.Embed(title="Avancement des membres", color=0x00ff00)
    
    for role_name in roles:
        role_obj = discord.utils.get(guild.roles, name=role_name)
        if role_obj:
            members = [m.mention for m in role_obj.members]
            embed.add_field(name=role_name, value=", ".join(members) if members else "Aucun", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Event on_ready ---
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"{client.user} connecté !")

# --- Run Bot ---
client.run(TOKEN)