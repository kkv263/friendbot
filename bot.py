import asyncio
import re
from datetime import datetime
from discord.ext import commands
from string import ascii_lowercase
from random import randint
from os import listdir
from os.path import isfile, join

from bfunc import *

bot = commands.Bot(command_prefix=commandPrefix, case_insensitive=True)
cogs_dir = "cogs"

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)
    await bot.change_presence(activity=discord.Game(name=f'D&D Friends | {commandPrefix} help'))

bot.remove_command('help')

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        if (ctx.command.name == 'rit' or ctx.command.name == 'mit'):
            msg = 'Woahhh, slow down partner! Try the command in the next {:.1f}s'.format(error.retry_after)
        if (ctx.command.name == 'addme'):
            msg = 'You have already added yourself to the timer'
        if (ctx.command.name == 'start'):
            msg = f"There is already a timer that has started in this channel! If you started the timer, type `{commandPrefix}timer stop` to stop the current timer"
        await ctx.channel.send(msg)
    else:
        raise error

@bot.command()
async def help(ctx):
    helpEmbed = discord.Embed (
      title='Available Commands'
    )
    helpEmbed.add_field(name=commandPrefix + "mit [optional name search]", value="Shows you a list of items from the Magic Item Table. React to the lists to view items. You can also search by name, for example: " + commandPrefix + "mit Cloak of Displacement" )
    helpEmbed.add_field(name=commandPrefix + "rit [optional name search]", value="Shows you a list of items from the Reward Item Table. React to the lists to view items.You can also search by name, for example: " + commandPrefix + "rit Moon-Touched Sword" )
    helpEmbed.add_field(name=commandPrefix + "rit random", value="Randomly awards you a Reward Item based on which tier and sub-tier you react to." )
    helpEmbed.add_field(name=commandPrefix + "reward [XhYm] [tier] ", value="Calculates player and DM rewards based on the time and tier you type in. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: " + commandPrefix + 'reward 3h30m Elite' )
    helpEmbed.add_field(name=commandPrefix + "timer start [optional game name]", value="Only available in **Game Rooms** and **Campaigns**. Start a timer to keep track of time and rewards for games. Only one timer per game room can be active at once.")
    helpEmbed.add_field(name=commandPrefix + "timer stamp", value="Only available in **Game Rooms** and **Campaigns**. View the elapsed time on the timer running. If you want to leave early from a game, this command allows you to calculate your rewards as well.")
    helpEmbed.add_field(name=commandPrefix + "timer addme", value="Only available in **Game Rooms** and **Campaigns**. If you join a game late, this command will add you to the timer running. Once the timer is stopped your rewards will be displayed at the end.")
    helpEmbed.add_field(name=commandPrefix + "timer removeme", value="Only available in **Game Rooms** and **Campaigns**. If you you wish to leave early, This command will calculate your awards for you and remove you from the timer (if you added yourself joining late)")
    helpEmbed.add_field(name=commandPrefix + "timer stop", value="Only available in **Game Rooms** and **Campaigns**. Stop a timer that you have started to show how much to CP, TP, and gp to reward the players who played the full duration of the game. Only the person who started the timer can stop it.")

    helpMsg = await ctx.channel.send(embed=helpEmbed)

if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)