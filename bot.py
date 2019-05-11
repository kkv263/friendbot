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
    await bot.change_presence(activity=discord.Game(name='D&D Friends | ' + commandPrefix + 'help'))

bot.remove_command('help')

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        if (ctx.command.name == 'rit' or ctx.command.name == 'mit'):
          msg = 'Woahhh, slow down partner! Try the command in the next {:.1f}s'.format(error.retry_after)
        if (ctx.command.name == 'timerstart'):
          msg = 'There is already a timer that has started in this channel! If you started the timer, type `' + commandPrefix + 'timerstop` to stop the current timer'
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
    helpEmbed.add_field(name=commandPrefix + "timerstart [optional game name]", value="Only available in **Game Rooms**. Start a timer to keep track of time and rewards for games. Only one timer per game room can be active at once.")
    helpEmbed.add_field(name=commandPrefix + "timerstop", value="Only available in **Game Rooms**. Stop a timer that you have started to show how much to CP, TP, and gp to reward the players who played the full duration of the game. Only the person who started the timer can stop it.")
    helpEmbed.add_field(name=commandPrefix + "reward [XhYm] [tier] ", value="Calculates player and DM rewards based on the time and tier you type in. The tier names are **Junior**, **Journey**, **Elite**, and **True**. Example: " + commandPrefix + 'reward 3h30m Elite' )

    helpMsg = await ctx.channel.send(embed=helpEmbed)

async def itemTable(tierArray, tierSubArray,sheet, ctx, queryString):
    def mitEmbedCheck(r, u):
        sameMessage = False
        if mitStart.id == r.message.id:
            sameMessage = True

        return (r.emoji in alphaEmojis[:alphaIndex] or r.emoji == '❌') and u == author and sameMessage

    def mitQueryCheck(r, u):
        sameMessage = False
        if mitQuery.id == r.message.id:
            sameMessage = True
        return (r.emoji in numberEmojis[:alphaIndex] or r.emoji == '❌') and u == author and sameMessage
    
    def mitItemEmbedCheck(m):
        return (m.content.lower() in [str(x) for x in range(1,len(mitResults) + 1)]) and m.channel == channel and m.author == author

    def getTier(choiceIndex):
        if choiceIndex >= tierArray[0] and choiceIndex < tierArray[1]:
            return 1
        elif choiceIndex >= tierArray[1] and choiceIndex < tierArray[2]:
            return 2
        elif choiceIndex >= tierArray[2]and choiceIndex < tierArray[3]:
            return 3
        else:
            return 4

    def getChoices(list):
        alphabet = 0
        choices = []
        for i in (list):
            if i != "":
                choices.append(alphaEmojis[alphabet])
                alphabet += 1
            else:
                choices.append('')
        return choices

    channel = ctx.channel
    author = ctx.author
    commandName = ctx.command.name
    commandUpper = commandName.upper() 

    if author.id == 194049802143662080:
      userName = 'Sir'
    else:
      userName = author.name

    mitEmbed = discord.Embed (
      title= f"{commandUpper} {queryString.capitalize()}",
      description= f"React with the corresponding bolded letter to access the {commandUpper}",
      colour = discord.Colour.orange(),
    )
    mitItemListEmbed = discord.Embed (
      colour = discord.Colour.orange(),
    )

    mitEmbed.set_author(name=userName, icon_url=author.avatar_url)
    mitItemListEmbed.set_author(name=userName, icon_url=author.avatar_url)
    mitEmbed.set_footer(text= "React with ❌ to cancel")

    if not queryString or queryString.lower() == 'random':
        choices = getChoices(tierSubArray)
        alphaIndex = 0
        for j in range(len(tierArray) - 1):
            k = tierArray[j]
            mitString = ""
            for k in range(k, tierArray[j+1] - 1 if tierArray[j+1] < len(tierSubArray) else len(tierSubArray)):
                mitString = mitString + alphaEmojis[alphaIndex] + ": " + tierSubArray[k] + '\n'
                if tierSubArray[k] != "":
                  alphaIndex += 1
            mitEmbed.add_field(name="Tier " + str(j+1), value=mitString, inline=True)

        mitStart = await ctx.channel.send(embed=mitEmbed)
        try:
            await mitStart.add_reaction('❌')
            mitChoice, mUser = await bot.wait_for('reaction_add', check=mitEmbedCheck,timeout=60.0)
        except asyncio.TimeoutError:
            await mitStart.delete()
            await channel.send(commandUpper + ' timed out!')
        else:
            if mitChoice.emoji == '❌':
                await mitStart.edit(embed=None, content=f"{commandUpper} canceled. Type `{commandPrefix}{commandName}` to open the {commandUpper}!")

                await mitStart.clear_reactions()
                return

            await asyncio.sleep(1) 
            await mitStart.clear_reactions()

            choiceIndex = choices.index(str(mitChoice.emoji)) 
            mitResults = sheet.col_values(choiceIndex + 1)

            def mitItemListCheck(r,u):
                sameMessage = False
                if mitStart.id == r.message.id:
                    sameMessage = True
                return sameMessage and u == author and (r.emoji == left or r.emoji == right or r.emoji == '❌' or r.emoji == back or r.emoji in numberEmojis)

            page = 0;
            perPage = 9
            tpNumber = mitResults.pop(2)
            mitResults.pop(0)
            mitResults.pop(0)
            numPages =((len(mitResults)) // perPage) + 1

            while True and not queryString:
                pageStart = perPage*page
                pageEnd = perPage * (page + 1) 
                mitResultsString = ""
                numberEmoji = 0
                for i in range(pageStart, pageEnd if pageEnd < (len(mitResults) - 1) else (len(mitResults)) ):
                    mitResultsString = mitResultsString + numberEmojis[numberEmoji] + ": " + mitResults[i] + "\n"
                    numberEmoji += 1
                mitItemListEmbed.add_field(name=f"[Tier {str(getTier(choiceIndex))}] {tpNumber}: React with the corresponding number", value=mitResultsString, inline=True)
                mitItemListEmbed.set_footer(text= f"Page {page+1} of {numPages} -- use {left} or {right} to navigate, {back} to go back, or ❌ to cancel")
                await mitStart.edit(embed=mitItemListEmbed) 
                if page != 0:
                    await mitStart.add_reaction(left) 
                if page + 1 != numPages:
                    await mitStart.add_reaction(right)

                await mitStart.add_reaction(back)
                await mitStart.add_reaction('❌')
                try:
                    react, pUser = await bot.wait_for("reaction_add", check=mitItemListCheck, timeout=90.0)
                except asyncio.TimeoutError:
                    await mitStart.delete()
                    await channel.send(f"{commandUpper} timed out!")
                else:
                    if react.emoji == left:
                        page -= 1
                    elif react.emoji == right:
                        page += 1
                    elif react.emoji == '❌':
                        await mitStart.edit(embed=None, content=f"{commandUpper} canceled. Type `{commandPrefix}{commandName}` to open the Magic Item Table!")
                        await mitStart.clear_reactions()
                        return
                    elif react.emoji == back:
                        await mitStart.delete()
                        await ctx.reinvoke()
                    elif react.emoji in numberEmojis:
                        break
                    mitItemListEmbed.clear_fields()
                    await mitStart.clear_reactions()
            
    await asyncio.sleep(1) 

    mitQuery = None

    if queryString.lower() == 'random':
        mitItem = sheet.cell(randint(0,len(mitResults)+ 3), choiceIndex + 1, value_render_option='FORMULA').value.split('"')
    elif queryString.lower() != 'random' and queryString:
        query = re.compile(queryString, re.IGNORECASE)
        gClient.login()
        queryResults = sheet.findall(query)


        if len(queryResults) == 1:
            choiceIndex = queryResults[0].col - 1
            mitItem = sheet.cell(queryResults[0].row, choiceIndex + 1, value_render_option='FORMULA').value.split('"')
        elif not queryResults:
            await ctx.channel.send(f"Your query `{queryString}` did not find any results. Try accessing the Magic Item Tables menu by using `{commandPrefix}{commandName}` or better your query.")
            return
        else:
            for j in list(queryResults):
                if j.row < 4:
                    queryResults.remove(j)

            queryResultsString = ""
            alphaIndex = len(queryResults) if len(queryResults) < 9 else 9

            if queryResults:
                for i in range(0, alphaIndex):
                    queryResultsString = queryResultsString + numberEmojis[i] + ": " +  queryResults[i].value +  '\n'

            mitQueryEmbed = discord.Embed (
              title = "Magic Item Tables",
              colour = discord.Colour.orange(),
            )
            mitQueryEmbed.set_author(name=userName, icon_url=author.avatar_url)
            mitQueryEmbed.add_field(name="React with the following number.", value=queryResultsString)
            mitQueryEmbed.set_footer(text= "React with ❌ to cancel")
            mitQuery = await ctx.channel.send(embed = mitQueryEmbed)
            try:
                await mitQuery.add_reaction('❌')
                qReaction, qUser = await bot.wait_for('reaction_add', check=mitQueryCheck,timeout=60.0)
            except asyncio.TimeoutError:
                await mitQuery.delete()
                await channel.send(commandUpper+ ' timed out!')
            else:
                if qReaction.emoji == '❌':
                    await mitQuery.edit(embed=None, content=f"{commandUpper} canceled. Type `{commandPrefix}{commandName}` to open the {commandUpper}")
                    await mitQuery.clear_reactions()
                    return
                queryResultsIndex = (int(str(qReaction.emoji)[0])) - 1
                choiceIndex = queryResults[queryResultsIndex].col - 1
                mitItem = sheet.cell(queryResults[queryResultsIndex].row, choiceIndex + 1, value_render_option='FORMULA').value.split('"')

    else:
        mitItem = sheet.cell((int(str(react.emoji)[0])) + pageStart + 3, choiceIndex + 1, value_render_option='FORMULA').value.split('"')

    tierColumn = str(getTier(choiceIndex))

    mitItemEmbed = discord.Embed (
      title = mitItem[3] + " - Tier " + tierColumn + ": " + sheet.cell(3,choiceIndex+1).value,
      colour = discord.Colour.orange(),
    )
    mitItemEmbed.set_author(name=userName, icon_url=author.avatar_url)
    mitItemEmbed.set_image(url=mitItem[1])

    if queryString.lower() != 'random' and queryString:
        if mitQuery:
            await mitQuery.edit(embed=mitItemEmbed)
            await mitQuery.clear_reactions()
        else:
            await ctx.channel.send(embed=mitItemEmbed)

    else:
        await mitStart.edit(embed=mitItemEmbed) 
        await mitStart.clear_reactions()

@commands.cooldown(1, 10, type=commands.BucketType.member)
@bot.command()
async def rit(ctx, *, queryString=""):
    await itemTable(ritTierArray, ritSubArray, ritSheet, ctx, queryString)
  
@commands.cooldown(1, 10, type=commands.BucketType.member)
@bot.command()
async def mit(ctx, *, queryString=""):
    await itemTable(tierArray, tpArray, sheet, ctx, queryString) 
            
if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cogs_dir) if isfile(join(cogs_dir, f))]:
        try:
            bot.load_extension(cogs_dir + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()

bot.run(token)