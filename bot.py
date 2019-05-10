import time
import asyncio
import re
import pytz
from datetime import datetime
from discord.ext import commands
from string import ascii_lowercase
from random import randint

from bfunc import *

bot = commands.Bot(command_prefix=commandPrefix, case_insensitive=True)

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)
    await bot.change_presence(activity=discord.Game(name='D&D Friends | ' + commandPrefix + 'help'))

bot.remove_command('help')

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error, commands.CommandOnCooldown):
        if (ctx.command.name == 'rit' or ctx.command.name == 'mit'):
          msg = 'Woahhh, slow down partner! Try the command in the next {:.2f}s'.format(error.retry_after)
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

async def itemTable(tierArray, tierSubArray,sheet, ctx, random):
    def mitEmbedCheck(r, u):
        sameMessage = False
        if mitStart.id == r.message.id:
            sameMessage = True

        return (str(r.emoji) in alphaEmojis[:alphaIndex] or str(r.emoji) == '❌') and u == ctx.author and sameMessage

    def mitQueryCheck(r, u):
        sameMessage = False
        if mitQuery.id == r.message.id:
            sameMessage = True
        return (str(r.emoji) in numberEmojis[:alphaIndex] or str(r.emoji) == '❌') and u == ctx.author and sameMessage
    
    def mitItemEmbedCheck(m):
        return (m.content.lower() in [str(x) for x in range(1,len(mitResults) + 1)]) and m.channel == channel and m.author == ctx.author

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

    if ctx.author.id == 194049802143662080:
      userName = 'Sir'
    else:
      userName = ctx.author.name

    mitEmbed = discord.Embed (
      title= ctx.command.name.upper() + " " + random.capitalize(),
      description= "React with the corresponding bolded letter to access the " + ctx.command.name.upper(),
      colour = discord.Colour.orange(),
    )
    mitItemListEmbed = discord.Embed (
      colour = discord.Colour.orange(),
    )

    mitEmbed.set_author(name=userName, icon_url=ctx.author.avatar_url)
    mitItemListEmbed.set_author(name=userName, icon_url=ctx.author.avatar_url)
    mitEmbed.set_footer(text= "React with ❌ to cancel")

    if not random or random.lower() == 'random':
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
            await channel.send(ctx.command.name.upper() + ' timed out!')
        else:
            # await mitStart.delete()
            if mitChoice.emoji == '❌':
                await mitStart.edit(embed=None, content=ctx.command.name.upper() + ' canceled. Type `' + commandPrefix + ctx.command.name + '` to open the '+ ctx.command.name.upper() + '!')

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
                return sameMessage and u == ctx.author and (str(r.emoji) == left or str(r.emoji) == right or str(r.emoji) == '❌' or str(r.emoji) == back or str(r.emoji) in numberEmojis)

            page = 0;
            perPage = 9
            tpNumber = mitResults.pop(2)
            mitResults.pop(0)
            mitResults.pop(0)
            numPages =((len(mitResults)) // perPage) + 1

            while True and not random:
                pageStart = perPage*page
                pageEnd = perPage * (page + 1) 
                mitResultsString = ""
                numberEmoji = 0
                for i in range(pageStart, pageEnd if pageEnd < (len(mitResults) - 1) else (len(mitResults)) ):
                    mitResultsString = mitResultsString + numberEmojis[numberEmoji] + ": " + mitResults[i] + "\n"
                    numberEmoji += 1
                mitItemListEmbed.add_field(name="[Tier "+ str(getTier(choiceIndex)) +  "] " + tpNumber + ": React with the corresponding number", value=mitResultsString, inline=True)
                mitItemListEmbed.set_footer(text= "Page " + str(page+1) + " of " + str(numPages) + " -- use " + left + " or " + right + " to navigate, " + back + " to go back, or ❌ to cancel")
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
                    await channel.send(ctx.command.name.upper()+ ' timed out!')
                else:
                    if react.emoji == left:
                        page -= 1
                    elif react.emoji == right:
                        page += 1
                    elif react.emoji == '❌':
                        await mitStart.edit(embed=None, content=ctx.command.name.upper() + ' canceled. Type `'+ commandPrefix + 'mit` to open the Magic Item Table!')
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

    if random.lower() == 'random':
        mitItem = sheet.cell(randint(0,len(mitResults)+ 3), choiceIndex + 1, value_render_option='FORMULA').value.split('"')
    elif random.lower() != 'random' and random:
        query = re.compile(random, re.IGNORECASE)
        gClient.login()
        queryResults = sheet.findall(query)


        if len(queryResults) == 1:
            choiceIndex = queryResults[0].col - 1
            mitItem = sheet.cell(queryResults[0].row, choiceIndex + 1, value_render_option='FORMULA').value.split('"')
        elif not queryResults:
            await ctx.channel.send('Your query did not find any results. Try accessing the Magic Item Tables menu by using ' + commandPrefix + '`' + ctx.command.name + '` or better your query.')
            return
        else:
            queryResultsString = ""
            alphaIndex = len(queryResults) if len(queryResults) < 9 else 9

            for j in list(queryResults):
                if j.row < 4:
                    queryResults.remove(j)

            for i in range(0, alphaIndex):
                queryResultsString = queryResultsString + numberEmojis[i] + ": " +  queryResults[i].value +  '\n'

            mitQueryEmbed = discord.Embed (
              title = "Magic Item Tables",
              colour = discord.Colour.orange(),
            )
            mitQueryEmbed.set_author(name=userName, icon_url=ctx.author.avatar_url)
            mitQueryEmbed.add_field(name="React with the following number.", value=queryResultsString)
            mitQueryEmbed.set_footer(text= "React with ❌ to cancel")
            mitQuery = await ctx.channel.send(embed = mitQueryEmbed)
            try:
                await mitQuery.add_reaction('❌')
                qReaction, qUser = await bot.wait_for('reaction_add', check=mitQueryCheck,timeout=60.0)
            except asyncio.TimeoutError:
                await mitQuery.delete()
                await channel.send(ctx.command.name.upper()+ ' timed out!')
            else:
                if qReaction.emoji == '❌':
                    await mitQuery.edit(embed=None, content=ctx.command.name.upper() + ' canceled. Type `'+ commandPrefix + 'mit` to open the Magic Item Table!')
                    await mitStart.clear_reactions()
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
    mitItemEmbed.set_author(name=userName, icon_url=ctx.author.avatar_url)
    mitItemEmbed.set_image(url=mitItem[1])

    if random.lower() != 'random' and random:
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
async def rit(ctx, *, random=""):
    await itemTable(ritTierArray, ritSubArray, ritSheet, ctx, random)
  
@commands.cooldown(1, 10, type=commands.BucketType.member)
@bot.command()
async def mit(ctx, *, queryString=""):
    await itemTable(tierArray, tpArray, sheet, ctx, queryString) 
            
@bot.command()
@commands.cooldown(1, float('inf'), type=commands.BucketType.channel)
async def timerstart(ctx, *, game="D&D Game"):
    def startEmbedcheck(r, u):
        return (str(r.emoji) == one or str(r.emoji) == two or str(r.emoji) == three or str(r.emoji) == four or str(r.emoji) == '❌' and u == ctx.author)

    # can try  checks
    if str(ctx.channel.category).lower() != gameCategory.lower():
        await ctx.channel.send('Try this command in a game channel!')
        return

        await ctx.channel.send(game)

    channel = ctx.channel
    user = ctx.author.display_name

    if ctx.author.id == 194049802143662080:
      userName = 'Sir'
    else:
      userName = ctx.author.name


    startEmbed = discord.Embed (
      colour = discord.Colour.blue(),
    )
    startEmbed.add_field(name='React with [1-4] for your type of game: **' + game + "**", value=one + ' New / Junior Friend [1-4]\n' + two + ' Journey Friend [5-10]\n' + three + ' Elite Friend [11-16]\n' + four + ' True Friend [17-20]' , inline=False)
    startEmbed.set_author(name=userName, icon_url=ctx.author.avatar_url)
    startEmbed.set_footer(text= "React with ❌ to cancel")

    embed = discord.Embed (
      title= 'Timer: ' + game,
      description=user + ', you stopped the timer.',
      colour = discord.Colour.blue(),
    )
    embed.set_author(name=userName, icon_url=ctx.author.avatar_url)

    try:
        startEmbedmsg = await channel.send(embed=startEmbed)
        await startEmbedmsg.add_reaction(one)
        await startEmbedmsg.add_reaction(two)
        await startEmbedmsg.add_reaction(three)
        await startEmbedmsg.add_reaction(four)
        await startEmbedmsg.add_reaction('❌')
        reaction, tUser = await bot.wait_for("reaction_add", check=startEmbedcheck, timeout=60)
    except asyncio.TimeoutError:
        await startEmbedmsg.delete()
        await channel.send('Timer timed out! Try starting the timer again.')
        timerstart.reset_cooldown(ctx)
    else:
        await asyncio.sleep(1) 
        await startEmbedmsg.clear_reactions()

        if str(reaction.emoji) == '❌':
            await startEmbedmsg.edit(embed=None, content='Timer canceled. Type `' + commandPrefix + 'timerstart` to start another timer!')
            timerstart.reset_cooldown(ctx)
            return

        role = roleArray[int(str(reaction.emoji)[0]) - 1]


        start = time.time()
        datestart= datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%m-%y %I:%M %p");
        await startEmbedmsg.edit(embed=None, content="Timer: Starting the timer for - " + "**" + game + "** " + "(" + role + " Friend). Type `" + commandPrefix + "timerstop` to stop the current timer" )

        msg = await bot.wait_for('message', check=lambda m: m.content == (commandPrefix + 'timerstop') and m.channel == channel and (m.author == ctx.author or "Mod Friend".lower() in [r.name.lower() for r in m.author.roles] or "Admins".lower() in [r.name.lower() for r in m.author.roles]))

        end = time.time()
        dateend=datetime.now(pytz.timezone(timezoneVar)).strftime("%b-%m-%y %I:%M %p");
        duration = end - start

        durationString = timeConversion(duration)

        treasureArray = calculateTreasure(duration,role)

        treasureString = str(treasureArray[0]) + " CP \n" + str(treasureArray[1]) + " TP \n" + str(treasureArray[2]) + " GP"
        dmTreasureString = str(treasureArray[3]) + " CP \n" + str(treasureArray[4]) + " TP \n" + str(treasureArray[5]) + " GP"

        embed.add_field(name="Time Started", value=datestart + " CDT", inline=True)
        embed.add_field(name="Time Ended", value=dateend +  " CDT", inline=True)
        embed.add_field(name="Time Duration", value=durationString, inline=False)
        embed.add_field(name=role +" Friend Rewards", value=treasureString, inline=True)
        await channel.send(embed=embed)
        timerstart.reset_cooldown(ctx)

@commands.cooldown(1, 5, type=commands.BucketType.member)
@bot.command()
async def reward(ctx, timeString, tier):
    seconds_per_unit = { "m": 60, "h": 3600 }
    def convert_to_seconds(s):
      return int(s[:-1]) * seconds_per_unit[s[-1]]

    if tier.lower().capitalize() not in roleArray:
        await ctx.channel.send(content='You did not type a valid tier. The valid tiers are: ' + ', '.join(roleArray))
        return

    lowerTimeString = timeString.lower()

    l = list((re.findall('.*?[hm]', lowerTimeString)))
    totalTime = 0
    for timeItem in l:
        totalTime += convert_to_seconds(timeItem)

    if totalTime == 0:
        await ctx.channel.send(content='You may have formatted the time incorrectly or calculated for 0. Try again with the correct format')
        return

    treasureArray = calculateTreasure(totalTime, tier)
    durationString = timeConversion(totalTime)
    treasureString = str(treasureArray[0]) + " CP, " + str(treasureArray[1]) + " TP, and " + str(treasureArray[2]) + " GP"
    dmTreasureString = str(treasureArray[3]) + " CP, " + str(treasureArray[4]) + " TP, and " + str(treasureArray[5]) + " GP"
    await ctx.channel.send(content='A ' + durationString + ' game would give a ' + tier.capitalize() + ' Friend\n\n**Player:** ' + treasureString + "\n" + "**DM:** " + dmTreasureString)

bot.run(token)