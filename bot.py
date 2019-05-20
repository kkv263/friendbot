import asyncio
from discord.ext import commands
from os import listdir
from os.path import isfile, join

from bfunc import *

bot = commands.Bot(command_prefix=commandPrefix, case_insensitive=True)
cogs_dir = "cogs"

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)
    await bot.change_presence(activity=discord.Game(name=f'D&D Friends | {commandPrefix}help'))

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
        if (ctx.command.name == 'add' or ctx.command.name == 'remove'):
            msg = 'Try the command in the next {:.1f}s'.format(error.retry_after)
        await ctx.channel.send(msg)
    else:
        raise error

@bot.command()
async def help(ctx):
    def helpCheck(r,u):
        sameMessage = False
        if helpMsg.id == r.message.id:
            sameMessage = True
        return sameMessage and u == ctx.author and (r.emoji == left or r.emoji == right)

    helpEmbedItems = discord.Embed() 
    helpEmbedTimer = discord.Embed()
    helpEmbedGuild = discord.Embed()

    helpList = [helpEmbedItems,helpEmbedTimer,helpEmbedGuild]

    helpEmbedItems.title = 'Available Item Table Commands'
    helpEmbedItems.add_field(name=commandPrefix + "mit [optional name search]", value="This shows you items from the Magic Item Table, sorted by tier and TP cost. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "mit Cloak of Displacement" )
    helpEmbedItems.add_field(name=commandPrefix + "rit [optional name search]", value="This shows you items from the Reward Item Table, sorted by tier and Minor / Major. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "rit Moon-Touched Sword" )
    helpEmbedItems.add_field(name=commandPrefix + "rit random", value="This randomly awards you a Reward Item based on which tier and sub-tier you react to." )

    helpEmbedTimer.title = 'Available Timer Commands'
    helpEmbedTimer.add_field(name=commandPrefix + "reward [XhYm] [tier] ", value="This calculates player and DM rewards based on the time and tier you typein. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: " + commandPrefix + 'reward 3h30m Elite' )
    helpEmbedTimer.add_field(name=commandPrefix + "timer start [optional game name]", value="This is only available in **Game Rooms** and **Campaigns**. This starts a timer to keep track of time and calculate rewards for your game. Only one timer per channel can be active at once, and the timer can only be stopped by the person who started it or a Mod.")
    helpEmbedTimer.add_field(name=commandPrefix + "timer stamp", value="Only available in **Game Rooms** and **Campaigns**. View the elapsed time on the timer running. Will also show the elapsed time for late players")
    helpEmbedTimer.add_field(name=commandPrefix + "timer addme", value="Only available in **Game Rooms** and **Campaigns**.  If you join a game late, this command will add you to the running timer. Your individual rewards will be displayed once the timer has been stopped.")
    helpEmbedTimer.add_field(name=commandPrefix + "timer removeme", value="Only available in **Game Rooms** and **Campaigns**. If you leave a game early, this command will remove you from the running timer and display your individual rewards for the time you played.")
    helpEmbedTimer.add_field(name=commandPrefix + "timer stop", value="Only available in **Game Rooms** and **Campaigns**. This stops a timer that you have started and shows how much to CP, TP, and gp to reward the players who played have not removed themselves from the timer. If players added themselves, it will display their rewards separately. The timer can only be stopped by the person who started it or a Mod.")

    helpEmbedGuild.title = 'Available Guild Commands'
    helpEmbedGuild.add_field(name=commandPrefix + "guild add [username#1234] ", value="This command is **case-sensitive** and is only available to Guildmasters. It allows a Guildmaster to add a member to one of the guilds that they are a Guildmaster of.")
    helpEmbedGuild.add_field(name=commandPrefix + "guild remove [username#1234] ", value="This command is **case-sensitive** and is only available to Guildmasters. It allows a Guildmaster to remove a member from one of the guilds that they are a Guildmaster of.")

    numPages = len(helpList)

    for i in range(0, len(helpList)):
        helpList[i].set_footer(text= f"Page {i+1} of {numPages} -- use {left} or {right} to navigate. ")

    helpMsg = await ctx.channel.send(embed=helpEmbedItems)
    page = 0
    while True:
        await helpMsg.add_reaction(left) 
        await helpMsg.add_reaction(right)
        try:
            hReact, hUser = await bot.wait_for("reaction_add", check=helpCheck, timeout=30.0)
        except asyncio.TimeoutError:
            await helpMsg.edit(content=f"Your help menu has timed out! I'll leave this page open for you. If you need to cycle through the list of commands again use `{commandPrefix}help`!")
            await helpMsg.clear_reactions()
            await helpMsg.add_reaction('💤')
            return
        else:

            if hReact.emoji == left:
                page -= 1
                if page < 0:
                    page = len(helpList) - 1
            if hReact.emoji == right:
                page += 1
                if page > len(helpList) - 1:
                    page = 0

            await helpMsg.edit(embed=helpList[page]) 
            await helpMsg.clear_reactions()


if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)