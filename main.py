import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import asyncio

# Configuration
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Fichier de configuration
CONFIG_FILE = "config.json"
TICKETS_FILE = "tickets.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_tickets(data):
    with open(TICKETS_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} slash commands synchronisées")
    except Exception as e:
        print(e)

# ============ SYSTÈME DE MESSAGES D'ARRIVÉE/DÉPARTS ============

@bot.event
async def on_member_join(member):
    config = load_config()
    guild_id = str(member.guild.id)
    
    if guild_id in config and "spawn_channel" in config[guild_id]:
        channel_id = config[guild_id]["spawn_channel"]
        channel = bot.get_channel(channel_id)
        
        if channel:
            message = config[guild_id].get("spawn_message", "Bienvenue {user}!")
            message = message.replace("{user}", member.mention)
            await channel.send(message)

@bot.event
async def on_member_remove(member):
    config = load_config()
    guild_id = str(member.guild.id)
    
    if guild_id in config and "bye_channel" in config[guild_id]:
        channel_id = config[guild_id]["bye_channel"]
        channel = bot.get_channel(channel_id)
        
        if channel:
            message = config[guild_id].get("bye_message", "Au revoir {user}!")
            message = message.replace("{user}", member.name)
            await channel.send(message)

@bot.tree.command(name="setspawn", description="Configure le channel de bienvenue")
@app_commands.describe(
    channel="Le channel pour les messages de bienvenue",
    message="Le message (utilise {user} pour la mention)"
)
async def setspawn(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["spawn_channel"] = channel.id
    config[guild_id]["spawn_message"] = message
    save_config(config)
    
    await interaction.response.send_message(f"✅ Channel de bienvenue configuré: {channel.mention}")

@bot.tree.command(name="setbye", description="Configure le channel d'au revoir")
@app_commands.describe(
    channel="Le channel pour les messages d'au revoir",
    message="Le message (utilise {user} pour le pseudo)"
)
async def setbye(interaction: discord.Interaction, channel: discord.TextChannel, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["bye_channel"] = channel.id
    config[guild_id]["bye_message"] = message
    save_config(config)
    
    await interaction.response.send_message(f"✅ Channel d'au revoir configuré: {channel.mention}")

# ============ COMMANDES ADMIN ============

@bot.tree.command(name="ban", description="Ban un utilisateur")
@app_commands.describe(
    user="L'utilisateur à ban",
    reason="Raison du ban"
)
async def ban(interaction: discord.Interaction, user: discord.User, reason: str = "Pas de raison"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission!", ephemeral=True)
        return
    
    try:
        await interaction.guild.ban(user, reason=reason)
        
        # Log
        embed = discord.Embed(title="🚫 Ban", color=discord.Color.red())
        embed.add_field(name="Utilisateur", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=False)
        embed.add_field(name="Date", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)
        
        # Envoyer le log
        log_channel = discord.utils.get(interaction.guild.channels, name="logs")
        if log_channel:
            await log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {user} a été banné!\n**Raison:** {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)

@bot.tree.command(name="to", description="Timeout un utilisateur")
@app_commands.describe(
    user="L'utilisateur",
    minutes="Durée en minutes",
    reason="Raison"
)
async def timeout(interaction: discord.Interaction, user: discord.User, minutes: int, reason: str = "Pas de raison"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission!", ephemeral=True)
        return
    
    try:
        member = await interaction.guild.fetch_member(user.id)
        duration = timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        
        # Log
        embed = discord.Embed(title="⏱️ Timeout", color=discord.Color.orange())
        embed.add_field(name="Utilisateur", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Durée", value=f"{minutes} minutes", inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=False)
        embed.add_field(name="Date", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)
        
        log_channel = discord.utils.get(interaction.guild.channels, name="logs")
        if log_channel:
            await log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {user} a un timeout de {minutes} min!\n**Raison:** {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="Exclure un utilisateur")
@app_commands.describe(
    user="L'utilisateur",
    reason="Raison"
)
async def kick(interaction: discord.Interaction, user: discord.User, reason: str = "Pas de raison"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ Tu n'as pas la permission!", ephemeral=True)
        return
    
    try:
        member = await interaction.guild.fetch_member(user.id)
        await member.kick(reason=reason)
        
        # Log
        embed = discord.Embed(title="👢 Kick", color=discord.Color.gold())
        embed.add_field(name="Utilisateur", value=f"{user.mention} ({user.id})", inline=False)
        embed.add_field(name="Raison", value=reason, inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=False)
        embed.add_field(name="Date", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)
        
        log_channel = discord.utils.get(interaction.guild.channels, name="logs")
        if log_channel:
            await log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ {user} a été exclu!\n**Raison:** {reason}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur: {e}", ephemeral=True)

# ============ SYSTÈME DE TICKETS ============

@bot.tree.command(name="ticket", description="Crée un panel de tickets")
async def ticket(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎫 Système de Tickets",
        description="Clique sur le bouton pour créer un ticket!",
        color=discord.Color.blue()
    )
    
    view = discord.ui.View()
    button = discord.ui.Button(label="Créer un ticket", style=discord.ButtonStyle.green)
    
    async def create_ticket(button_interaction: discord.Interaction):
        # Créer un channel ticket
        category = discord.utils.get(interaction.guild.categories, name="Tickets")
        if not category:
            category = await interaction.guild.create_category("Tickets")
        
        channel = await category.create_text_channel(
            name=f"ticket-{button_interaction.user.name}",
            topic=f"Ticket créé par {button_interaction.user.mention}"
        )
        
        # Permissions
        await channel.set_permissions(button_interaction.user, read_messages=True, send_messages=True)
        
        embed_ticket = discord.Embed(
            title="🎫 Nouveau Ticket",
            description=f"Bienvenue {button_interaction.user.mention}!\nDécris ton problème ci-dessous.",
            color=discord.Color.green()
        )
        
        close_view = discord.ui.View()
        close_btn = discord.ui.Button(label="Fermer le ticket", style=discord.ButtonStyle.red)
        
        async def close_ticket(close_interaction: discord.Interaction):
            await channel.delete()
        
        close_btn.callback = close_ticket
        close_view.add_item(close_btn)
        
        await channel.send(embed=embed_ticket, view=close_view)
        await button_interaction.response.send_message(f"✅ Ticket créé: {channel.mention}", ephemeral=True)
    
    button.callback = create_ticket
    view.add_item(button)
    
    await interaction.response.send_message(embed=embed, view=view)

# ============ SYSTÈME D'AVIS AVEC BOUTON ============

class AvisModal(discord.ui.Modal, title="Donner un avis"):
    avis = discord.ui.TextInput(label="Ton avis", style=discord.TextStyle.paragraph, required=True)
    note = discord.ui.TextInput(label="Note (1-5)", style=discord.TextStyle.short, required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        config = load_config()
        guild_id = str(interaction.guild.id)
        
        if guild_id not in config or "avis_channel" not in config[guild_id]:
            await interaction.response.send_message("❌ Channel d'avis non configuré!", ephemeral=True)
            return
        
        avis_channel = bot.get_channel(config[guild_id]["avis_channel"])
        if not avis_channel:
            await interaction.response.send_message("❌ Channel introuvable!", ephemeral=True)
            return
        
        # Créer l'embed d'avis
        embed_avis = discord.Embed(
            title="⭐ Nouvel Avis",
            color=discord.Color.gold()
        )
        embed_avis.add_field(name="Utilisateur", value=interaction.user.mention, inline=False)
        embed_avis.add_field(name="Note", value=self.note.value, inline=False)
        embed_avis.add_field(name="Avis", value=self.avis.value, inline=False)
        embed_avis.add_field(name="Date", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)
        
        await avis_channel.send(embed=embed_avis)
        
        # Créer une facture
        if guild_id in config and "facture_channel" in config[guild_id]:
            facture_channel = bot.get_channel(config[guild_id]["facture_channel"])
            if facture_channel:
                embed_facture = discord.Embed(
                    title="📄 Facture Créée",
                    description=f"Suite à l'avis de {interaction.user.mention}",
                    color=discord.Color.blue()
                )
                embed_facture.add_field(name="Avis reçu", value="✅", inline=False)
                embed_facture.add_field(name="Date", value=datetime.now().strftime("%d/%m/%Y %H:%M"), inline=False)
                
                await facture_channel.send(embed=embed_facture)
        
        await interaction.response.send_message("✅ Avis envoyé! Merci!", ephemeral=True)

@bot.tree.command(name="avis", description="Crée un panel d'avis")
async def avis_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="⭐ Laisser un Avis",
        description="Clique sur le bouton pour laisser un avis!",
        color=discord.Color.gold()
    )
    
    view = discord.ui.View()
    button = discord.ui.Button(label="Laisser un avis", style=discord.ButtonStyle.gold)
    
    async def open_modal(button_interaction: discord.Interaction):
        await button_interaction.response.send_modal(AvisModal())
    
    button.callback = open_modal
    view.add_item(button)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="setavis", description="Configure le channel d'avis")
@app_commands.describe(channel="Le channel pour les avis")
async def setavis(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["avis_channel"] = channel.id
    save_config(config)
    
    await interaction.response.send_message(f"✅ Channel d'avis configuré: {channel.mention}")

@bot.tree.command(name="setfacture", description="Configure le channel de facturation")
@app_commands.describe(channel="Le channel pour les factures")
async def setfacture(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Tu dois être admin!", ephemeral=True)
        return
    
    config = load_config()
    guild_id = str(interaction.guild.id)
    
    if guild_id not in config:
        config[guild_id] = {}
    
    config[guild_id]["facture_channel"] = channel.id
    save_config(config)
    
    await interaction.response.send_message(f"✅ Channel de facture configuré: {channel.mention}")

# ============ COMMANDES UTILES ============

@bot.tree.command(name="ping", description="Ping du bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="help", description="Affiche l'aide")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 Aide du Bot", color=discord.Color.blue())
    embed.add_field(name="/setspawn", value="Configure les messages de bienvenue", inline=False)
    embed.add_field(name="/setbye", value="Configure les messages d'au revoir", inline=False)
    embed.add_field(name="/ban", value="Ban un utilisateur (Admin)", inline=False)
    embed.add_field(name="/to", value="Timeout un utilisateur (Admin)", inline=False)
    embed.add_field(name="/kick", value="Exclut un utilisateur (Admin)", inline=False)
    embed.add_field(name="/ticket", value="Crée un panel de tickets (Admin)", inline=False)
    embed.add_field(name="/avis", value="Crée un panel d'avis (Admin)", inline=False)
    embed.add_field(name="/setavis", value="Configure le channel d'avis (Admin)", inline=False)
    embed.add_field(name="/setfacture", value="Configure le channel de facture (Admin)", inline=False)
    
    await interaction.response.send_message(embed=embed)

# Lancer le bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
