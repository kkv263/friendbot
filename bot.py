import asyncio
import traceback
from discord.ext import commands
from os import listdir
from os.path import isfile, join
from itertools import cycle

from bfunc import *

cogs_dir = "cogs"

async def change_status():
      await bot.wait_until_ready()
      statusLoop = cycle(statuses)

      while not bot.is_closed():
          current_status = next(statusLoop)
          await bot.change_presence(activity=discord.Activity(name=current_status, type=discord.ActivityType.watching))
          await asyncio.sleep(5)

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)
    # bot.loop.create_task(change_status())

    #secret area channel
    # channel = bot.get_channel(577611798442803205) 
    # await channel.send('Hello I have restarted uwu')
  
bot.remove_command('help')

@bot.event
async def on_command_error(ctx,error):
    # TODO: Fix for char create and guild create
    msg = None
    print(ctx.invoked_with)
    print(error)

    if isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
        await ctx.channel.send("There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. ")
        bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
        return

    elif isinstance(error, commands.CommandOnCooldown):
        if error.retry_after == float('inf'):
            await ctx.channel.send(f"Sorry, the command `{commandPrefix}{ctx.invoked_with}` is already in progress, please complete the command before trying again.")
        else:
            await ctx.channel.send(f"Sorry, the command `{commandPrefix}{ctx.invoked_with}` is on cooldown for you!\nTry the command in the next " + "{:.1f}seconds".format(error.retry_after))
        return

    elif ctx.cog is not None and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
        return

    elif isinstance(error, commands.CommandNotFound):
        await ctx.channel.send(f'Sorry, the command `{commandPrefix}{ctx.invoked_with}` is not valid, please try again!')

    else:
        ctx.command.reset_cooldown(ctx)
        await traceBack(ctx,error)

@bot.command()
async def help(ctx, *, pageString=''):
    def helpCheck(r,u):
        sameMessage = False
        if helpMsg.id == r.message.id:
            sameMessage = True
        return (r.emoji in numberEmojis[:numPages]) and u == ctx.author

    helpEmbedMenu = discord.Embed()
    helpEmbedChar = discord.Embed()
    helpEmbedItems = discord.Embed() 
    helpEmbedTimerOne = discord.Embed()
    helpEmbedShop = discord.Embed()
    helpEmbedTp = discord.Embed()
    helpEmbedGuild = discord.Embed()

    page = 0
    if 'char' in pageString or 'character' in pageString:
        page = 1
    elif 'timer' in pageString in pageString:
        page = 2
    elif 'itemtable' in pageString:
        page = 3
    elif 'shop' in pageString:
        page = 4
    elif 'tp' in pageString:
        page = 4
    elif 'guild' in pageString:
        page = 6


    helpList = [helpEmbedMenu, helpEmbedChar, helpEmbedTimerOne, helpEmbedItems, helpEmbedShop, helpEmbedTp, helpEmbedGuild]

    helpEmbedMenu.title = 'Bot Friend Commands - Table of Contents:'
    helpEmbedMenu.description = 'Please react to the group of commands you would like to see and gain more knowledge about.'
    helpEmbedMenu.add_field(name="1️⃣ Character Commands", value="Manages your character and help with character creation and character leveling process.", inline=False)
    helpEmbedMenu.add_field(name="2️⃣ Timer (Pre/Post Game) Commands", value="Provide a timer that is essential to games as a DM or a player. ", inline=False)
    helpEmbedMenu.add_field(name="3️⃣ Item Table Commands", value="Provide lookup for the Magic Item Table (MIT) or the Reward Item Table (RIT)", inline=False)
    helpEmbedMenu.add_field(name="4️⃣ Shop Commands", value="Purchase or sell items.", inline=False)
    helpEmbedMenu.add_field(name="5️⃣ TP Commands", value="Purchase magic items.", inline=False)
    helpEmbedMenu.add_field(name="6️⃣ Guild Commands", value="Manage your guild as a guildmaster, or join / leave a guild", inline=False)

    helpEmbedChar.title = 'Available Character Commands'
    helpEmbedChar.add_field(name=commandPrefix + 'create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "MIT items" "RIT items"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name='MULTICLASS Creation -' + commandPrefix + 'create "character name" level "race" "class1 # / class2 #..." level " "background" STR DEX CON INT WIS CHA "MIT items" "RIT items"', value="Creates your character.", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'respec "character name" "new character name" level "race" "class" "background" STR DEX CON INT WIS CHA "MIT items" "RIT items"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'stats', value="Shows your TOTAL games played with all characters, your noodles, and all your characters. You must play in at least one game before this command works for you.", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'info "character name"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'image "character name" url', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'inventory "character name"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'retire "character name"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'attune "character name" "magic item"', value="TODO: Add description here", inline=False)
    helpEmbedChar.add_field(name=commandPrefix + 'unattune "character name" "magic item"', value="TODO: Add description here", inline=False)
    
    helpEmbedTimerOne.title = 'Available Timer Commands: Before starting a timer; pt1.\n(Only available in **Game Rooms** and **Campaigns**)'
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer prep #guild1 #guild2(*optional) "@player1, @player2, @player3,..." gamename(*optional) ', value="Preps a game for @player's and #guilds. This allows the DM and players to signup characters to recieve rewards.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer cancel', value="Cancels the current timer prep.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer signup "charactername" "consumable list"', value="Signs up your character to participate and be eligible for rewards", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer add @player', value="Adds a player to the roster so they can signup their character", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer remove @player', value="Removes a player from the roster", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + 'timer start', value=f"**Followed by **:`{commandPrefix}timer prep` - Starts a timer to keep track of time and calculate rewards for your game. Only one timer per channel can be active at once, and the timer can only be stopped by the person who started it or a Mod.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer resume", value="Resumes the last running timer that was started, and behaves identical to " + commandPrefix + "timer start.", inline=False)

    helpEmbedTimerOne.add_field(name="=@=@=@=@=@=", value="During a Timer; (Only available in **Game Rooms** and **Campaigns**)", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer transfer", value="Transfer the timer from the owner to another user. The new owner will be able to stop the timer.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer add @player \"charactername\" \"consumables\"", value="**DM Only**: If you join a game late, this command will add @player to the running timer. Their individual rewards will be displayed once the timer has been stopped.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer addme charactername \"consumables\"", value="If you join a game late, this command will add you to the running timer. Their individual rewards will be displayed once the timer has been stopped.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer remove @player", value="**DM Only**: Remove the user mentioned from the running timer and display their individual rewards for the time they played.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer removeme", value="If you leave a game early, this command will remove you from the running timer and display your individual rewards for the time you played.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer reward @player \"rewards\"", value="**DM Only**: Rewards @player item(s) from the RIT. Reward limits depend on your Noodle Role.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "- Consumable", value="Consumes the consumable your character uses and deletes it from their inventory", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "timer stop", value="**DM Only**: Stops a timer that you have started and shows how much to CP, TP, and gp to reward the players who played have not removed themselves from the timer. If players added themselves, it will display their rewards separately. The timer can only be stopped by the person who started it or a Mod.", inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "reward [XhYm] [tier] ", value="This calculates player and DM rewards based on the time and tier you typein. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: " + commandPrefix + 'reward 3h30m Elite', inline=False)
    helpEmbedTimerOne.add_field(name=commandPrefix + "log edit gameid, summary", value="TODO: ADd description", inline=False)

    helpEmbedItems.title = 'Available Item Table Commands'
    helpEmbedItems.add_field(name=commandPrefix + "mit [optional name search]", value="This shows you items from the Magic Item Table, sorted by tier and TP cost. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "mit Cloak of Displacement" )
    helpEmbedItems.add_field(name=commandPrefix + "rit [optional name search]", value="This shows you items from the Reward Item Table, sorted by tier and Minor / Major. React to the lists to change pages or view items. You can also search by name, for example: " + commandPrefix + "rit Moon-Touched Sword" )
    helpEmbedItems.add_field(name=commandPrefix + "rit random", value="This randomly awards you a Reward Item based on which tier and sub-tier you react to." )

    helpEmbedShop.title = 'Available Shop Commands'
    helpEmbedShop.add_field(name=commandPrefix + 'shop buy "character name" "item" #', value="TODO: Add description here", inline=False)
    helpEmbedShop.add_field(name=commandPrefix + 'shop sell "character name" "item" #', value="TODO: Add description here", inline=False)
    helpEmbedShop.add_field(name=commandPrefix + 'shop copy "character name" "spell" #', value="TODO: Add description here", inline=False)
    helpEmbedShop.add_field(name=commandPrefix + 'shop proficiency "character name"', value="TODO: Add description here", inline=False)

    helpEmbedTp.title = 'Available TP Commands'
    helpEmbedTp.add_field(name=commandPrefix + 'tp buy "character name" "MIT Item" #', value="TODO: Add description here", inline=False)
    helpEmbedTp.add_field(name=commandPrefix + 'tp discard "character name"', value="TODO: Add description here", inline=False)
    helpEmbedTp.add_field(name=commandPrefix + 'tp abandon "character name" tier', value="TODO: Add description here", inline=False)

    helpEmbedGuild.title = 'Available Guild Commands'
    helpEmbedGuild.add_field(name=commandPrefix + 'guild create "guild name" @role #channel', value="TODO: Add description here", inline=False)
    helpEmbedGuild.add_field(name=commandPrefix + 'guild fund "character name" gp "guild name"', value="TODO: Add description here", inline=False)
    helpEmbedGuild.add_field(name=commandPrefix + 'guild info "guild name"', value="TODO: Add description here", inline=False)
    helpEmbedGuild.add_field(name=commandPrefix + 'guild leave "character name"', value="TODO: Add description here", inline=False)
    helpEmbedGuild.add_field(name=commandPrefix + 'guild rep "character name" #', value="TODO: Add description here", inline=False)

    numPages = len(helpList)

    for i in range(0, len(helpList)):
        helpList[i].set_footer(text= f"Page {i+1} of {numPages}")

    helpMsg = await ctx.channel.send(embed=helpList[page])
    if page == 0:
        for num in range(0,numPages-1): await helpMsg.add_reaction(numberEmojis[num])

    try:
        hReact, hUser = await bot.wait_for("reaction_add", check=helpCheck, timeout=30.0)
    except asyncio.TimeoutError:
        await helpMsg.edit(content=f"Your help menu has timed out! I'll leave this page open for you. If you need to cycle through the list of commands again use `{commandPrefix}help`!")
        await helpMsg.clear_reactions()
        await helpMsg.add_reaction('💤')
        return
    else:
        await helpMsg.edit(embed=helpList[int(hReact.emoji[0])])
        await helpMsg.clear_reactions()


    # while True:
    #     await helpMsg.add_reaction(left) 
    #     await helpMsg.add_reaction(right)
    #     try:
    #         hReact, hUser = await bot.wait_for("reaction_add", check=helpCheck, timeout=30.0)
    #     except asyncio.TimeoutError:
    #         await helpMsg.edit(content=f"Your help menu has timed out! I'll leave this page open for you. If you need to cycle through the list of commands again use `{commandPrefix}help`!")
    #         await helpMsg.clear_reactions()
    #         await helpMsg.add_reaction('💤')
    #         return
    #     else:
    #         if hReact.emoji == left:
    #             page -= 1
    #             if page < 0:
    #                 page = len(helpList) - 1
    #         if hReact.emoji == right:
    #             page += 1
    #             if page > len(helpList) - 1:
    #                 page = 0

    #         await helpMsg.edit(embed=helpList[page]) 
    #         await helpMsg.clear_reactions()


if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)