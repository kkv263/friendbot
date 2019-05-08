import time
import asyncio
from datetime import datetime
from discord.ext import commands
from string import ascii_lowercase

from bfunc import *

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print('We have logged in as ' + bot.user.name)

bot.remove_command('help')

@bot.command()
async def help(ctx):
		helpEmbed = discord.Embed (
			title='Available Commands'
		)
		helpEmbed.add_field(name="!mit", value="Shows you items from the Magic Item Table" )
		helpEmbed.add_field(name="!rit", value="(Coming Soon) Shows you items from the DM Rewards Item Table" )
		helpEmbed.add_field(name="!timerstart", value="Command Available in Game rooms. Start a timer to keep track of time and rewards for games." )

		helpMsg = await ctx.channel.send(embed=helpEmbed)


@bot.command()
async def rit(ctx):
    channel = ctx.channel

    mitEmbed = discord.Embed (
      title= 'Reward Item Table',
      description= "Type the corresponding bolded letter to access the Reward Item Table",
      colour = discord.Colour.orange(),
    )
    mitItemEmbed = discord.Embed (
      colour = discord.Colour.orange(),
    )

@bot.command()
async def mit(ctx):
    def mitEmbedCheck(r, u):
        return (str(r.emoji) in alphaEmojis or str(r.emoji) == '❌') and u == ctx.author
    
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

    mitEmbed = discord.Embed (
      title= 'Magic Item Table',
      description= "React with the corresponding bolded letter to access the Magic Item Table",
      colour = discord.Colour.orange(),
    )
    mitItemListEmbed = discord.Embed (
      colour = discord.Colour.orange(),
    )

    mitEmbed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    mitItemListEmbed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

    choices = getChoices(tpArray)
    alphaIndex = 0
    for j in range(len(tierArray) - 1):
        k = tierArray[j]
        mitString = ""
        for k in range(k, tierArray[j+1] - 1):
            mitString = mitString + alphaEmojis[alphaIndex] + ": " + tpArray[k] + '\n'
            if tpArray[k] != "":
              alphaIndex += 1
        mitEmbed.add_field(name="Tier " + str(j+1), value=mitString, inline=True)

    mitStart = await ctx.channel.send(embed=mitEmbed)
    try:
        await mitStart.add_reaction('❌')
        mitChoice, mUser = await bot.wait_for('reaction_add', check=mitEmbedCheck,timeout=60.0)
    except asyncio.TimeoutError:
        await mitStart.delete()
        await channel.send('Magic Item Table timed out!')
    else:
        # await mitStart.delete()
        if mitChoice.emoji == '❌':
            await mitStart.edit(embed=None, content='Magic Item Table canceled. Type `!mit` to open the Magic Item Table!')
            await mitStart.clear_reactions()
            return

        await asyncio.sleep(1) 
        await mitStart.clear_reactions()

        choiceIndex = choices.index(str(mitChoice.emoji)) 
        mitResults = sheet.col_values(choiceIndex + 1)

        def mitItemListCheck(r,u):
            return u == ctx.author and (str(r.emoji) == left or str(r.emoji) == right or str(r.emoji) == '❌' or str(r.emoji) in numberEmojis)

        page = 0;
        perPage = 10
        tpNumber = mitResults.pop(2)
        mitResults.pop(0)
        mitResults.pop(0)
        numPages =((len(mitResults)) // perPage) + 1

        while True:
            pageStart = perPage*page
            pageEnd = perPage * (page + 1) 
            mitResultsString = ""
            numberEmoji = 0
            for i in range(pageStart, pageEnd if pageEnd < (len(mitResults) - 1) else (len(mitResults)) ):
                mitResultsString = mitResultsString + numberEmojis[numberEmoji] + ": " + mitResults[i] + "\n"
                numberEmoji += 1
            mitItemListEmbed.add_field(name="[Tier "+ str(getTier(choiceIndex)) +  "] " + tpNumber + ": React with the corresponding number", value=mitResultsString, inline=True)
            mitItemListEmbed.set_footer(text= "Page " + str(page+1) + " of " + str(numPages) + " -- use ⏪ or ⏩ to navigate")
            await mitStart.edit(embed=mitItemListEmbed) 
            if page != 0:
                await mitStart.add_reaction(left) 
            if page + 1 != numPages:
                await mitStart.add_reaction(right)

            await mitStart.add_reaction('❌')
            try:
                react, pUser = await bot.wait_for("reaction_add", check=mitItemListCheck, timeout=90.0)
            except asyncio.TimeoutError:
                await mitStart.delete()
                await channel.send('Magic Item Table timed out!')
            else:
                if react.emoji == left:
                    page -= 1
                elif react.emoji == right:
                    page += 1
                elif react.emoji == '❌':
                    await mitStart.edit(embed=None, content='Magic Item Table canceled. Type `!mit` to open the Magic Item Table!')
                    await mitStart.clear_reactions()
                    return
                elif react.emoji in numberEmojis:
                    break
                mitItemListEmbed.clear_fields()
                await mitStart.clear_reactions()

        await asyncio.sleep(1) 

        mitItem = sheet.cell((int(str(react.emoji)[0])) + pageStart + 3, choiceIndex + 1, value_render_option='FORMULA').value.split('"')

        mitItemEmbed = discord.Embed (
          title = mitItem[3],
          colour = discord.Colour.orange(),
        )
        mitItemEmbed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        mitItemEmbed.set_image(url=mitItem[1])

        await mitStart.edit(embed=mitItemEmbed) 
        await mitStart.clear_reactions()
            
@bot.command()
@commands.cooldown(1, 100, type=commands.BucketType.channel)
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
    lastmsg = await channel.history().get(author__name='friend')

    startEmbed = discord.Embed (
      title= 'React with [1-4] for your type of game: **' + game + "**\nReact with [X] to cancel",
      colour = discord.Colour.blue(),
    )
    startEmbed.add_field(name="[1]: ", value='New/Junior' , inline=True)
    startEmbed.add_field(name="[2]", value='Journey Friend' , inline=True)
    startEmbed.add_field(name="[3]", value='Elite Friend' , inline=True)
    startEmbed.add_field(name="[4]", value='True Friend' , inline=True)
    startEmbed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

    embed = discord.Embed (
      title= 'Timer: ' + game,
      description=user + ', you stopped the timer.',
      colour = discord.Colour.blue(),
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

    # If the last message from the bot start's with Timer: will exit function (if someone typed !timerstart again or something)
    if lastmsg is not None:
        if lastmsg.content.startswith('Timer:'):
          await channel.send("Timer: There is a timer already running, type `!timerstop` to stop the current timer") 
          return

    try:
        startEmbedmsg = await channel.send(embed=startEmbed)
        await startEmbedmsg.add_reaction(one)
        await startEmbedmsg.add_reaction(two)
        await startEmbedmsg.add_reaction(three)
        await startEmbedmsg.add_reaction(four)
        await startEmbedmsg.add_reaction('❌')
        reaction, tUser = await bot.wait_for("reaction_add", check=startEmbedcheck, timeout=30)
    except asyncio.TimeoutError:
        await startEmbedmsg.delete()
        await channel.send('Timer timed out! Try starting the timer again.')
        timerstart.reset_cooldown(ctx)
    else:
        await asyncio.sleep(1) 
        await startEmbedmsg.clear_reactions()

        if str(reaction.emoji) == '❌':
            await startEmbedmsg.edit(embed=None, content='Timer canceled. Type `!timerstart` to start another timer!')
            timerstart.reset_cooldown(ctx)
            return

        role = roleArray[int(str(reaction.emoji)[0]) - 1]

        start = time.time()
        datestart= datetime.now().strftime("%Y-%m-%d %H:%M");
        await startEmbedmsg.edit(embed=None, content="Timer: Starting the timer for - " + "**" + game + "** " + "(" + role + " Friend). Type `!timerstop` to stop the current timer" )

        msg = await bot.wait_for('message', check=lambda m: m.content == '!timerstop' and m.content != '!timerstart' and m.channel == channel and m.author == ctx.author)

        end = time.time()
        dateend=datetime.now().strftime("%Y-%m-%d %H:%M");
        duration = end - start

        durationString = (time.strftime('%H Hours and %M Minutes', time.gmtime(duration)))

        treasureArray = calculateTreasure(duration,role)

        treasureString = str(treasureArray[0]) + " CP \n" + str(treasureArray[1]) + " TP \n" + str(treasureArray[2]) + " GP"

        embed.add_field(name="Time Started", value=datestart, inline=True)
        embed.add_field(name="Time Ended", value=dateend, inline=True)
        embed.add_field(name="Time Duration", value=durationString, inline=False)
        embed.add_field(name=role +" Friend Awards", value=treasureString, inline=False)
        await channel.send(embed=embed)
        timerstart.reset_cooldown(ctx)

bot.run(token)