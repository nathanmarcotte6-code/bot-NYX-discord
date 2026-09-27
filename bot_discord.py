import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command(name="hello")
async def hello(ctx):
    await ctx.send(f"Salut {ctx.author.mention}! 👋")

@bot.command(name="info")
async def user_info(ctx):
    user = ctx.author
    embed = discord.Embed(title="Informations utilisateur", color=discord.Color.blue())
    embed.add_field(name="Nom", value=user.name, inline=False)
    embed.add_field(name="ID", value=user.id, inline=False)
    embed.add_field(name="Créé le", value=user.created_at.strftime("%d/%m/%Y"), inline=False)
    await ctx.send(embed=embed)

@bot.command(name="roll")
async def roll(ctx, sides: int = 6):
    import random
    result = random.randint(1, sides)
    await ctx.send(f"🎲 Résultat: **{result}** (1-{sides})")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Commande non trouvée. Utilise `!help` pour voir les commandes.")
    else:
        await ctx.send(f"❌ Erreur: {error}")

bot.run("TON_TOKEN_ICI")
