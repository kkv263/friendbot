import discord
import asyncio
import re
from random import randint
from discord.ext import commands

from bfunc import tierArray, tpArray, ritTierArray, ritSubArray, ritSheet, sheet, numberEmojis, alphaEmojis,left,right,back, refreshTime, refreshKey, commandPrefix


class ItemTables(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    async def itemTableFunc(self, tierArray, tierSubArray, sheet, ctx, queryString):
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
            userName = author.display_name

        colour = randint(0, 0xffffff)

        mitEmbed = discord.Embed (
            title= f"{commandUpper} {queryString.capitalize()}",
            description= f"React with the corresponding bolded letter to access the {commandUpper}",
            colour = colour,
        )
        mitItemListEmbed = discord.Embed (
            colour = colour,
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
                mitChoice, mUser = await self.bot.wait_for('reaction_add', check=mitEmbedCheck,timeout=60.0)
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
            
                refreshKey(refreshTime)
                mitResults = sheet.col_values(choiceIndex + 1)

                def mitItemListCheck(r,u):
                    sameMessage = False
                    if mitStart.id == r.message.id:
                        sameMessage = True
                    return sameMessage and u == author and (r.emoji == left or r.emoji == right or r.emoji == '❌' or r.emoji == back or r.emoji in numberEmojis[:numberEmoji])

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
                    await mitStart.add_reaction(left) 
                    await mitStart.add_reaction(right)
                    await mitStart.add_reaction(back)
                    await mitStart.add_reaction('❌')
                    try:
                        react, pUser = await self.bot.wait_for("reaction_add", check=mitItemListCheck, timeout=90.0)
                    except asyncio.TimeoutError:
                        await mitStart.delete()
                        await channel.send(f"{commandUpper} timed out!")
                        return
                    else:
                        if react.emoji == left:
                            page -= 1
                            if page < 0:
                              page = numPages - 1;
                        elif react.emoji == right:
                            page += 1
                            if page > numPages - 1: 
                              page = 0
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
            refreshKey(refreshTime)
            mitItem = sheet.cell(randint(1,len(mitResults)) + 3, choiceIndex + 1, value_render_option='FORMULA').value.split('"')
        elif queryString.lower() != 'random' and queryString:
            query = re.compile(queryString, re.IGNORECASE)
            refreshKey(refreshTime)
            queryResults = sheet.findall(query)


            if len(queryResults) == 1:
                choiceIndex = queryResults[0].col - 1
                refreshKey(refreshTime)
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
                    colour = colour,
                )
                mitQueryEmbed.set_author(name=userName, icon_url=author.avatar_url)
                mitQueryEmbed.add_field(name="React with the following number.", value=queryResultsString)
                mitQueryEmbed.set_footer(text= "React with ❌ to cancel")
                mitQuery = await ctx.channel.send(embed = mitQueryEmbed)
                try:
                    await mitQuery.add_reaction('❌')
                    qReaction, qUser = await self.bot.wait_for('reaction_add', check=mitQueryCheck,timeout=60.0)
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
                    refreshKey(refreshTime)
                    mitItem = sheet.cell(queryResults[queryResultsIndex].row, choiceIndex + 1, value_render_option='FORMULA').value.split('"')

        else:
            refreshKey(refreshTime)
            mitItem = sheet.cell((int(str(react.emoji)[0])) + pageStart + 3, choiceIndex + 1, value_render_option='FORMULA').value.split('"')

        tierColumn = str(getTier(choiceIndex))

        refreshKey(refreshTime)
        mitItemEmbed = discord.Embed (
            title = mitItem[3] + " - Tier " + tierColumn + ": " + sheet.cell(3,choiceIndex+1).value,
            colour = colour,
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
    @commands.command()
    async def mit(self,ctx, *, queryString=""):
        itemTable = self.bot.get_cog('ItemTables')
        await itemTable.itemTableFunc(tierArray, tpArray, sheet, ctx, queryString)

    @commands.cooldown(1, 10, type=commands.BucketType.member)
    @commands.command()
    async def rit(self, ctx, *, queryString=""):
        itemTable = self.bot.get_cog('ItemTables')
        await itemTable.itemTableFunc(ritTierArray, ritSubArray, ritSheet, ctx, queryString)
    


def setup(bot):
    bot.add_cog(ItemTables(bot))
