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
    msg = None
    print(ctx.invoked_with)
    print(ctx.command.parent)
    print(error)
    
    if isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
        await ctx.channel.send("There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. ")
        bot.get_command(ctx.invoked_with).reset_cooldown(ctx)
        return
    elif ctx.cog is not None and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
        return
        
    elif isinstance(error, commands.CommandOnCooldown):
        commandParent = ctx.command.parent
        if commandParent is None:
            commandParent = ''
        else:
            commandParent = commandParent.name + " "

        if error.retry_after == float('inf'):
            await ctx.channel.send(f"Sorry, the command **`{commandPrefix}{commandParent}{ctx.invoked_with}`** is already in progress, please complete the command before trying again.")
        else:
            await ctx.channel.send(f"Sorry, the command **`{commandPrefix}{commandParent}{ctx.invoked_with}`** is on cooldown for you! Try the command in the next " + "{:.1f}seconds".format(error.retry_after))
        return



    elif isinstance(error, commands.CommandNotFound):
        await ctx.channel.send(f'Sorry, the command **`{commandPrefix}{ctx.invoked_with}`** is not valid, please try again!')

    else:
        ctx.command.reset_cooldown(ctx)
        await traceBack(ctx,error)

@bot.command()
async def help(ctx, *, pageString=''):
    def helpCheck(r,u):
        sameMessage = False
        if helpMsg.id == r.message.id:
            sameMessage = True
        return (r.emoji in numberEmojis[:numPages]) and u == ctx.author and sameMessage

    helpEmbedMenu = discord.Embed()
    helpEmbedChar = discord.Embed()
    helpEmbedItems = discord.Embed() 
    helpEmbedTimerOne = discord.Embed()
    helpEmbedTimerTwo = discord.Embed()
    helpEmbedShop = discord.Embed()
    helpEmbedTp = discord.Embed()
    helpEmbedGuild = discord.Embed()

    page = 0
    if 'char' in pageString or 'character' in pageString:
        page = 1
    elif 'timer2' in pageString:
        page = 3
    elif 'timer1' in pageString or 'timer' in pageString:
        page = 2
    elif 'itemtable' in pageString:
        page = 4
    elif 'shop' in pageString:
        page = 5
    elif 'tp' in pageString:
        page = 6
    elif 'guild' in pageString:
        page = 7


# MAIN HELP MENU ($help)

    helpList = [helpEmbedMenu, helpEmbedChar, helpEmbedTimerOne, helpEmbedTimerTwo, helpEmbedItems, helpEmbedShop, helpEmbedTp, helpEmbedGuild]

    helpEmbedMenu.title = 'Bot Friend Commands - Table of Contents'
    helpEmbedMenu.description = 'Please react to the group of commands you would like to see and gain more knowledge about.'
    helpEmbedMenu.add_field(name=f"1️⃣ Character Commands\n{commandPrefix}help char", value="Manage all facets of your character(s).", inline=False)
    helpEmbedMenu.add_field(name=f"2️⃣ Timer (Pre/Post-Quest) Commands\n{commandPrefix}help timer1", value="Prepare and manage the timer before and after the quest.", inline=False)
    helpEmbedMenu.add_field(name=f"3️⃣ Timer (During Quest) Commands\n{commandPrefix}help timer2", value="Manage the timer during a quest.", inline=False)
    helpEmbedMenu.add_field(name=f"4️⃣ Item Table Commands\n{commandPrefix}help itemtable", value="Look up items on the Magic Item Table (MIT) and Reward Item Table (RIT).", inline=False)
    helpEmbedMenu.add_field(name=f"5️⃣ Shop Commands\n{commandPrefix}help shop", value="Purchase or sell items.", inline=False)
    helpEmbedMenu.add_field(name=f"6️⃣ TP Commands\n{commandPrefix}help tp", value="Acquire magic items.", inline=False)
    helpEmbedMenu.add_field(name=f"7️⃣ Guild Commands\n{commandPrefix}help guild", value="Manage your guild as a Guildmaster or join/leave a guild.", inline=False)


# CHARACTER COMMANDS MENU ($help char)

    helpEmbedChar.title = 'Character Commands'

    helpEmbedChar.add_field(name=f'▫️ User Information\n{commandPrefix}user', value="View the total number of one-shots that you’ve played in, the number of Noodles you have, the guilds you’ve created, and a list of your characters.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Character Creation\n{commandPrefix}create "character name" level "race" "class" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"', value="Create a character with the specified parameters.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Multiclass Character Creation\n{commandPrefix}create "character name" total level "race" "class1 level / class2 level, [...]" "background" STR DEX CON INT WIS CHA "magic item1, magic item2, [...]" "reward item1, reward item2, [...]"', value="Create a multiclass character with the specified parameters.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Leveling Up\n{commandPrefix}levelup "character name"\n[{commandPrefix}lvlup, {commandPrefix}lvl, {commandPrefix}lv]', value="Level up the specified character to the next level (if possible).", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Respec\n{commandPrefix}respec "character name" "new character name" "race" "class" "background" STR DEX CON INT WIS CHA', value="Respec the specified character into a single class if they are under level 5. TP and gp will be assigned to them based on the amount of CP they have and their entire inventory will be reset.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Multiclass Respec\n{commandPrefix}respec "character name" "new character name" "race" "class1 level / class2 level / [...]" "background" STR DEX CON INT WIS CHA', value="Respec the specified character into a multiclass if they are under level 5.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Character Information\n{commandPrefix}info "character name"\n[{commandPrefix}char, {commandPrefix}i]', value="View the stats and general information of the specified character.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Character Inventory\n{commandPrefix}inventory "character name"\n[{commandPrefix}inv, {commandPrefix}bag]', value="View the inventory of the specified character.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Character Image\n{commandPrefix}image "character name" "URL"\n[{commandPrefix}img]', value="Add an image to the specified character's information page using a URL. Images must be SFW (Safe For Work)!", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Attunement\n{commandPrefix}attune "character name" "magic item"\n[{commandPrefix}att]', value="Attune to the specified magic item with the specified character.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Unattunement\n{commandPrefix}unattune "character name" "magic item"\n[{commandPrefix}unatt, {commandPrefix}uatt]', value="Unattune from the specified magic item with the specified character.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Retire\n{commandPrefix}retire "character name"', value="Permanently retire the specified character. You will not be able to access them.", inline=False)

    helpEmbedChar.add_field(name=f'▫️ Death Options\n{commandPrefix}death "character name"', value=f"Decide the fate of the specified character who died during a quest.", inline=False)


# PRE-QUEST TIMER COMMANDS MENU ($help timer1)

    helpEmbedTimerOne.title = f"Pre-Quest Timer Commands\n{commandPrefix}timer, {commandPrefix}t"

    helpEmbedTimerOne.add_field(name=f'▫️ Preparing the Timer (DM)\n{commandPrefix}timer prep "@player1, @player2, @player3, [...]" quest name', value="Prepare a timer with a list of mentioned players so they can sign up with their characters. The DM can also sign up with a character.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Signing Up (Player)\n{commandPrefix}timer signup "character name" "consumable1, consumable2, [...]"', value="Sign up with a character and their consumables if the player was mentioned when the timer was prepared.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Adding Players (DM)\n{commandPrefix}timer add @player', value="Add the mentioned player to the roster after the DM has already prepared the timer so they can sign up.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Removing Players (DM)\n{commandPrefix}timer remove @player', value="Remove a player from the roster.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Adding Guilds (DM)\n{commandPrefix}timer guild #guild1, #guild2, [...]', value="Add a maximum of three guilds to their quest.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Cancelling the Timer (DM)\n{commandPrefix}timer cancel', value="Cancel the prepared timer.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Starting the Timer (DM)\n{commandPrefix}timer start', value="Start the prepared timer.", inline=False)


# DURING AND POST-QUEST TIMER COMMANDS MENU ($help timer2)

    helpEmbedTimerTwo.title = f"Timer Commands (During a Quest)\n{commandPrefix}timer, {commandPrefix}t"

    helpEmbedTimerTwo.add_field(name=f'▫️ Adding Yourself (Player)\n{commandPrefix}timer addme "character name" "consumable1, consumable2, [...]"', value="Add yourself to the running timer with the specified character and their consumables. The DM must approve this command.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Using Consumables (Player)\n- "consumable"', value="Use one of the consumables that their character brought into the quest.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Removing Yourself (Player)\n{commandPrefix}timer removeme', value="Remove yourself from the running timer.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Adding Players (DM)\n{commandPrefix}timer add @player "charactername" "consumables"', value="Add the mentioned player to the running timer with the specified character and their consumables.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Removing Players (DM)\n{commandPrefix}timer remove @player', value="Remove the mentioned player from the running timer.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Awarding Reward Items (DM)\n{commandPrefix}timer reward @player "reward item1, reward item2, [...]"', value="Award one or more reward item from the Reward Item Table to the mentioned player.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Character Death (DM)\n{commandPrefix}timer death @player', value="Mark the mentioned player as dead.", inline=False)

    helpEmbedTimerTwo.add_field(name=f'▫️ Stopping the Timer (DM)\n{commandPrefix}timer stop', value="Stop the running timer.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Resuming the Timer (DM)\n{commandPrefix}timer resume', value="Resume the timer if it was interrupted for any reason.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Submitting a Session Log (DM)\n{commandPrefix}session log questid summary', value="Submit a session log with a summary for the running timer which the DM just stopped. The quest ID is an 18-digit code. The summary must include how it fulfilled two of the three pillars of D&D and how it involved any listed guilds. It will also require approval by the Mods.", inline=False)

    helpEmbedTimerOne.add_field(name=f'▫️ Calculating Rewards (Misc.)\n{commandPrefix}reward [XhYm] [tier]', value=f"Look up the rewards that a specified amount of time would give for the specified tier. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: {commandPrefix}reward 3h30m Elite", inline=False)


# ITEM TABLE CCOMMANDS MENU ($help itemtable)

    helpEmbedItems.title = 'Item Table Commands'
    helpEmbedItems.add_field(name=f'▫️ Magic Item Table Lookup\n{commandPrefix}mit [optional name search]', value=f"Look up items from the Magic Item Table, sorted by tier and TP cost. React to the lists to change pages or view items. You can also search by name, for example: {commandPrefix}mit Folding Boat", inline=False)
    helpEmbedItems.add_field(name=f'▫️ Reward Item Table Lookup\n{commandPrefix}rit [optional name search]', value=f"Look up items from the Reward Item Table, sorted by tier and Minor/Major. React to the lists to change pages or view items. You can also search by name, for example: {commandPrefix}rit Clockwork Dog", inline=False)
    helpEmbedItems.add_field(name=f'▫️ Random Reward Item\n{commandPrefix}rit random', value=f"Display a random reward item based on the tier and sub-tier you selected.", inline=False)


# SHOP COMMANDS MENU ($help shop)

    helpEmbedShop.title = 'Shop Commands'

    helpEmbedShop.add_field(name=f'▫️ Buying an Item\n{commandPrefix}shop buy "character name" "item" #', value="Purchase a specified number of a single item from the shop. Purchasing a spell scroll uses the following format: \"Spell Scroll (spell name)\"", inline=False)

    helpEmbedShop.add_field(name=f'▫️ Selling a Mundane Item\n{commandPrefix}shop sell "character name" "item" #', value="Sell a specified number of a single mundane item to the shop", inline=False)

    helpEmbedShop.add_field(name=f'▫️ Copying a Spell Scroll\n{commandPrefix}shop copy "character name" "spell name"', value="Copy a spell scroll into your character's spellbook if they have access to one.", inline=False)

    helpEmbedShop.add_field(name=f'▫️ Training Extra Competencies\n{commandPrefix}proficiency training "character name"\n[{commandPrefix}prof]', value="Learn a language or gain proficiency in a tool (or a skill later on).", inline=False)

    helpEmbedShop.add_field(name=f'▫️ Training Noodle Competencies\n{commandPrefix}proficiency noodle "character name"\n[{commandPrefix}prof]', value="Learn a language or gain proficiency in a tool (or a skill later on) but with a discount and extra benefits due to your Noodle role!", inline=False)


# TP COMMANDS MENU ($help tp)

    helpEmbedTp.title = 'TP Commands'

    helpEmbedTp.add_field(name=f'▫️ Acquiring a Magic Item\n{commandPrefix}tp buy "character name" "magic item"', value="Put TP towards a magic item or acquire it with gp.", inline=False)

    helpEmbedTp.add_field(name=f'▫️ Discarding an Incomplete Magic Item\n{commandPrefix}tp discard "character name"', value="Discard an incomplete magic item with partial TP towards it in addition to all TP that has been put towards it.", inline=False)

    helpEmbedTp.add_field(name=f'▫️ Abandoning Leftover TP\n{commandPrefix}tp abandon "character name" tier', value="Abandon leftover TP in the tier of your choosing.", inline=False)


# GUILD COMMANDS MENU ($help guild)

    helpEmbedGuild.title = 'Guild Commands'

    helpEmbedGuild.add_field(name=f'▫️ Viewing a Guild\n{commandPrefix}guild info "guild name"', value="View the specified guild's roster and reputation in its bank. If the guild has yet to be funded, it will instead show the amount gp that it requires before it will be officially opened.", inline=False)

    helpEmbedGuild.add_field(name=f'▫️ Joining a Guild\n{commandPrefix}guild join "character name" "guild name"', value="Join the specified guild with the specified character.", inline=False)

    helpEmbedGuild.add_field(name=f'▫️ Upgrading Your Rank\n{commandPrefix}guild rankup "character name"', value="Upgrade the specified character's rank in the guild that they are a member of.", inline=False)

    helpEmbedGuild.add_field(name=f'▫️ Leaving a Guild\n{commandPrefix}guild leave "character name"', value="Leave the guild which the specified character is a member of.", inline=False)

    helpEmbedGuild.add_field(name=f'▫️ Creating a Guild\n{commandPrefix}guild create "character name" "guild name" @role #channel', value="Create a guild which will require funding in order to officially open.", inline=False)

    helpEmbedGuild.add_field(name=f'▫️ Funding a Guild\n{commandPrefix}guild fund "character name" "guild name" gp', value="Fund and join a newly-created guild which still requires funding in order to officially open.", inline=False)



    numPages = len(helpList)

    for i in range(0, len(helpList)):
        helpList[i].set_footer(text= f"Page {i+1} of {numPages}")

    helpMsg = await ctx.channel.send(embed=helpList[page])
    if page == 0:
        for num in range(0,numPages-1): await helpMsg.add_reaction(numberEmojis[num])

    try:
        hReact, hUser = await bot.wait_for("reaction_add", check=helpCheck, timeout=30.0)
    except asyncio.TimeoutError:
        await helpMsg.edit(content=f"Your help menu has timed out! I'll leave this page open for you. Use the first command if you need to cycle through help menu again or use any of the other commands to view a specific help menu:\n```yaml\n{commandPrefix}help char\n{commandPrefix}help timer1\n{commandPrefix}help timer2\n{commandPrefix}help itemtable\n{commandPrefix}help shop\n{commandPrefix}help tp\n{commandPrefix}help guild```")
        await helpMsg.clear_reactions()
        await helpMsg.add_reaction('💤')
        return
    else:
        await helpMsg.edit(embed=helpList[int(hReact.emoji[0])])
        await helpMsg.clear_reactions()


if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)
