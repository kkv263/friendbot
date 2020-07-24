import discord
import asyncio
from discord.utils import get        
from discord.ext import commands
from bfunc import  numberEmojis, numberEmojisMobile, commandPrefix, checkForChar, checkForGuild, noodleRoleArray, db, traceBack

class Guild(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
       

    @commands.group(aliases=['g'])
    async def guild(self, ctx):	
        pass

    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send(f'Sorry, the command `{commandPrefix}{ctx.invoked_with}` requires an additional keyword to the command or is invalid, please try again!')
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'charName':
                msg = "You're missing your character name in the command. "
            elif error.param.name == "guildName":
                msg = "You're missing the guild name in the command."
            elif error.param.name == "roleName":
                msg = "You're missing the @role for the guild you want to create"
            elif error.param.name == "channelName":
                msg = "You're missing the #channel for the guild you want to create. "
            elif error.param.name == "gpName":
                msg = "You're missing the amount of gp you want to fund the guild." 
        elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
            msg = "There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. "

        if msg:
            if ctx.command.name == "create":
                msg += f"Please follow this format:\n`{commandPrefix}guild create \"character name\" \"guild name\" @rolename #channelname`.\n"
            elif ctx.command.name == "info":
                msg += f"Please follow this format:\n`{commandPrefix}guild info \"guild name\"`.\n"
            elif ctx.command.name == "fund":
                msg += f"Please follow this format:\n`{commandPrefix}guild fund \"character name\" gp \"guild name\"`.\n"
            elif ctx.command.name == "join":
                msg += f"Please follow this format:\n`{commandPrefix}guild join \"character name\" \"guild name\"`.\n"
            elif ctx.command.name == "leave":
                msg += f"Please follow this format:\n`{commandPrefix}guild leave \"character name\"`.\n"
            elif ctx.command.name == "rep":
                msg += f"Please follow this format:\n`{commandPrefix}guild rep \"character name\" sparkles` \n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    # TODO: Limit to category and make sure channel + role line up.
    async def create(self,ctx, charName, guildName, roleName="", channelName=""):
        channel = ctx.channel
        author = ctx.author
        guildEmbed = discord.Embed()
        guildCog = self.bot.get_cog('Guild')

        guildRole = ctx.message.role_mentions
        guildChannel = ctx.message.channel_mentions

        roles = [r.name for r in ctx.author.roles]

        if 'Guildmaster' not in roles:
            await channel.send(f"You do not have the Guild Master role to use this command.")
            return 

        if guildRole == list() or guildChannel == list():
            await channel.send(f"A guild role or guild channel must be supplied.")
            return 
            

        roles = author.roles
        noodleRole = None
        for r in roles:
            if r.name in noodleRoleArray and r.name != 'Good Noodle':
                noodleRole = r

        if noodleRole:
            noodleLimit = noodleRoleArray.index(noodleRole.name) - 1
            usersCollection = db.users
            userRecords = usersCollection.find_one({"User ID": str(author.id)})
            if userRecords: 
                charDict, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)
                if charDict:
                    charID = charDict['_id']
                    if 'Guilds' not in userRecords: 
                        userRecords['Guilds'] = 0

                    if userRecords['Guilds'] > noodleLimit:
                        await channel.send(f"{author.display_name}, your current role `{noodleRole.name}` does not let you create another guild.")
                        return

                    if 'Guild' in charDict:
                        await channel.send(f"{charDict['Name']} is already a part of `{charDict['Guild']}` and won't be able to create another guild.")
                        return

                    userRecords['Guilds'] += 1

                    guildExists = await checkForGuild(ctx,guildName) 

                    if guildExists:
                        await channel.send(f"There is already a guild by the name of `{guildName}`. Please try creating a guild with a different name.")
                        return

                    # True, Ascended, and Immortal Noodles start with 10, 20, and 30 :sparkles: in their total/bank to start.
                    totalRep = (noodleRoleArray.index(noodleRole.name) - 1 ) * 10
                        
                    guildsDict = {'Role ID': str(guildRole[0].id), 'Channel ID': str(guildChannel[0].id), 'Name': guildName, 'Funds': 0, 'Guildmaster': charDict['Name'], 'Guildmaster ID': str(author.id), 'Reputation': totalRep, 'Total Reputation': totalRep}
                    await author.add_roles(guildRole[0], reason=f"Created guild {guildName}")

                    try:
                        playersCollection = db.players
                        guildsCollection = db.guilds
                        playersCollection.update_one({'_id': charID}, {"$set": {"Guild": guildName, 'Guild Rank': 1}})
                        usersCollection.update_one({"User ID": str(author.id)}, {"$set": {"Guilds": userRecords['Guilds']}})
                        guildsCollection.insert_one(guildsDict)
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        guildEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your guild again.")
                    else:
                        print('Success')

                        guildEmbed.title = f"Guild Creation: {guildName}"
                        guildEmbed.description = f"{charDict['Name']} has created **{guildName}**!\n\nIn order for the guild to open officially, 6000gp must be put into the guild.\n\nOther characters, including your character, can fund the guild - `{commandPrefix}guild fund [charactername] [x] {guildName}` (x = amount of GP to fund)\n\nThe guild's status can be checked with `{commandPrefix}guild info {guildName}`\n\nCurrent Funds: 0"
                        if guildEmbedmsg:
                            await guildEmbedmsg.clear_reactions()
                            await guildEmbedmsg.edit(embed=guildEmbed)
                        else: 
                            guildEmbedmsg = await channel.send(embed=guildEmbed)
                          
            else:
                await channel.send(f'{author.display_name} you will need to play at least one game with a character before you can create a guild.')
                return

        else:
            await channel.send(f'{author.display_name}, you need the `Elite Noodle` role or higher to create a guild. ')
            return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def info(self,ctx, guildName): 
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedEmbedmsg = None

        guildRecords = await checkForGuild(ctx,guildName) 

        if guildRecords:
            guildRank = ""
            if guildRecords['Total Reputation'] > 60:
                guildRank = "Rank 4 (Masterwork)"
            elif guildRecords['Total Reputation'] > 30:
                guildRank = "Rank 3 (Large)"
            elif guildRecords['Total Reputation'] > 10:
                guildRank = "Rank 2 (Medium)"
            else:
                guildRank = "Rank 1 (Small)"

            guildEmbed.title = f"{guildRecords['Name']} - {guildRank}" 
            guildEmbed.add_field (name= 'Guildmaster', value=f"{guild.get_member(int(guildRecords['Guildmaster ID'])).mention} **{guildRecords['Guildmaster']}**\n", inline=False)

            playersCollection = db.players
            guildMembers = list(playersCollection.find({"Guild": guildRecords['Name']}))

            guildMemberStr = ""
            for g in guildMembers:
                guildMemberStr += f"{guild.get_member(int(g['User ID'])).mention} **{g['Name']}** [Rank {g['Guild Rank']}]\n"
            guildEmbed.add_field(name="Members", value=guildMemberStr)

            if guildRecords['Funds'] < 6000:
                guildEmbed.add_field(name="Funds", value=f"{guildRecords['Funds']}gp / 6000gp.\n**{6000 - guildRecords['Funds']}gp** left to open the guild!", inline=False)
            else:
                guildEmbed.add_field(name="Reputation", value=f"Total Reputation: {guildRecords['Total Reputation']} :sparkles:\nBank: {guildRecords['Reputation']} :sparkles:", inline=False)


            await channel.send(embed=guildEmbed)

        else:
            await channel.send(f'The guild `{guildName}` does not exist. Please try again')
            return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def fund(self,ctx, charName,  gpFund, guildName): 
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedEmbedmsg = None

        def guildEmbedCheck(r, u):
            sameMessage = False
            if guildEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            guildRecords = await checkForGuild(ctx,guildName) 

            if guildRecords:
                if guildRecords['Funds'] >= 6000:
                    await channel.send(f"`{guildRecords['Name']}` is not expecting any funds. This guild has already been opened.")
                    return

                if 'Guild' in charRecords:
                    if charRecords['Guild'] != guildRecords['Name']:
                        await channel.send(f"{charRecords['Name']} cannot fund `{guildRecords['Name']}` because they belong to the guild `{charRecords['Guild']}`.")
                        return

                gpNeeded = 0
                refundGP = 0

                if charRecords['Level'] < 5:
                    gpNeeded = 200
                elif charRecords['Level'] < 11:
                    gpNeeded = 400
                elif charRecords['Level'] < 17:
                    gpNeeded = 600
                elif charRecords['Level'] < 21:
                    gpNeeded = 800

                if (float(gpFund)) > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} currently has {charRecords['GP']} and does not have {gpFund}gp to fund `{guildRecords['Name']}`.")
                    return
                     

                if gpNeeded > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} does not have the minimum {gpNeeded}gp to fund `{guildRecords['Name']}`.")
                    return

                if gpNeeded > float(gpFund):
                    await channel.send(f"{charRecords['Name']} needs to donate at least the minimum {gpNeeded}gp to fund `{guildRecords['Name']}`.")
                    return

                        
                guildEmbed.title = f"Fund Guild: {guildRecords['Name']}"
                guildEmbed.description = f"Are you sure you want to fund **{guildRecords['Name']}**?\n:warning: **{charRecords['Name']} will automatically join {guildRecords['Name']} upon funding.**\n\n✅ : Yes\n\n❌: Cancel"


                if guildEmbedmsg:
                    await guildEmbedmsg.edit(embed=guildEmbed)
                else:
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                await guildEmbedmsg.add_reaction('✅')
                await guildEmbedmsg.add_reaction('❌')
                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await guildEmbedmsg.delete()
                    await channel.send(f'Guild canceled. Use `{commandPrefix}guild join` command and try again!')
                    return
                else:
                    await guildEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await guildEmbedmsg.edit(embed=None, content=f"Shop canceled. Use `{commandPrefix}tp buy` command and try again!")
                        await guildEmbedmsg.clear_reactions()
                        return

                guildRecords['Funds'] += float(gpFund) 

                if  guildRecords['Funds'] >= 6000:
                    refundGP = guildRecords['Funds'] - 6000

                print(guild)
                print(guildRecords)

                newGP = (charRecords['GP'] - float(gpFund)) + refundGP
                await author.add_roles(guild.get_role(int(guildRecords['Role ID'])), reason=f"Funded guild {guildRecords['Name']}")


                try:
                    playersCollection = db.players
                    guildsCollection = db.guilds
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'Guild': guildRecords['Name'], 'GP':newGP, 'Guild Rank': 1}})
                    guildsCollection.update_one({'Name': guildRecords['Name']}, {"$set": {'Funds':guildRecords['Funds']}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    guildEmbed.title = f"Fund Guild: {guildRecords['Name']}"
                    guildEmbed.description = f"{charRecords['Name']} has funded **{guildRecords['Name']}** with {gpFund}gp.\nIf the amount puts the guild's funds over 6000, the leftover is refunded.\n\n**Current Guild Funds:** {guildRecords['Funds']}gp / 6000gp\n\n**Current gp**: {newGP}\n"
                    if guildRecords['Funds'] >= 6000:
                        guildEmbed.description += f"Congratulations! :tada: **{guildRecords['Name']}**  is officially open!"
                    if guildEmbedmsg:
                        await guildEmbedmsg.edit(embed=guildEmbed)
                    else:
                        guildEmbedmsg = await channel.send(embed=guildEmbed)

            else:
                await channel.send(f'The guild `{guildName}` does not exist. Please try again.')
                return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def join(self,ctx, charName, guildName): 
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedEmbedmsg = None

        def guildEmbedCheck(r, u):
            sameMessage = False
            if guildEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            if 'Guild' in charRecords:
                await channel.send(f"{charRecords['Name']} cannot join any guilds because they belong to the guild `{charRecords['Guild']}`.")
                return

            guildRecords = await checkForGuild(ctx,guildName) 

            if guildRecords:
                if guildRecords['Funds'] < 6000:
                    await channel.send(f"`{guildRecords['Name']}` is not open to join.")
                    return

                gpNeeded = 0

                if charRecords['Level'] < 5:
                    gpNeeded = 200
                elif charRecords['Level'] < 11:
                    gpNeeded = 400
                elif charRecords['Level'] < 17:
                    gpNeeded = 600
                elif charRecords['Level'] < 21:
                    gpNeeded = 800

                if (float(gpFund)) > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} currently has {charRecords['GP']} and does not have {gpFund}gp to fund `{guildRecords['Name']}`.")
                    return

                if gpNeeded > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} does not have the minimum {gpNeeded}gp to join `{guildRecords['Name']}`.")
                    return
                        
                guildEmbed.title = f"Joining Guild: {guildRecords['Name']}"
                guildEmbed.description = f"Are you sure you want to join **{guildRecords['Name']}**?\n\n✅ : Yes\n\n❌: Cancel"

                if guildEmbedmsg:
                    await guildEmbedmsg.edit(embed=guildEmbed)
                else:
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                await guildEmbedmsg.add_reaction('✅')
                await guildEmbedmsg.add_reaction('❌') 

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await guildEmbedmsg.delete()
                    await channel.send(f'Guild canceled. Use `{commandPrefix}guild join` command and try again!')
                    return
                else:
                    await guildEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Use `{commandPrefix}guild join` command and try again!")
                        await guildEmbedmsg.clear_reactions()
                        return

                newGP = (charRecords['GP'] - float(gpNeeded)) 
                await author.add_roles(guild.get_role(guildRecords['Role ID']), reason=f"Joined guild {guildName}")

                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'Guild': guildRecords['Name'], 'GP':newGP, 'Guild Rank': 1}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    guildEmbed.description = f"{charRecords['Name']} has joined **{guildRecords['Name']}**\n\n**Current gp**: {newGP}\n"
                    if guildEmbedmsg:
                        await guildEmbedmsg.edit(embed=guildEmbed)
                    else:
                        guildEmbedmsg = await channel.send(embed=guildEmbed)
                
            else:
                await channel.send(f'The guild `{guildName}` does not exist. Please try again.')
                return

            
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def rankup(self,ctx, charName):
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedEmbedmsg = None

        def guildEmbedCheck(r, u):
            sameMessage = False
            if guildEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            if 'Guild' not in charRecords:
                await channel.send(f"{charRecords['Name']} cannot upgrade their guild rank because they currently do not belong to a guild.")
                return

            guildRecords = await checkForGuild(ctx, charRecords['Guild']) 
            
            if guildRecords:

                if guildRecords['Funds'] < 6000: 
                    await channel.send(f"{charRecords['Name']} cannot upgrade their guild rank because `{charRecords['Guild']}` is not officially open and still needs funding.")
                    return

                if charRecords['Guild Rank'] > 3:
                    await channel.send(f"{charRecords['Name']} is already at the max rank and does not need to upgrade anymore.")
                    return

                elif charRecords['Guild Rank'] == 3:
                    starsAdded = 6
                    if guildRecords['Total Reputation'] < 60:
                        await channel.send(f"{charRecords['Name']} cannot upgrade because their guild `{guildRecords['Name']}` does not have the `Masterwork Upgrade`.")
                        return
                elif charRecords['Guild Rank'] == 2:
                    starsAdded = 3
                    if guildRecords['Total Reputation'] < 30:
                        await channel.send(f"{charRecords['Name']} cannot upgrade because their guild `{guildRecords['Name']}`, does not have the `Large Upgrade`.")
                        return
                elif charRecords['Guild Rank'] == 1:
                    starsAdded = 1
                    if guildRecords['Total Reputation'] < 10:
                        await channel.send(f"{charRecords['Name']} cannot upgrade because their guild `{guildRecords['Name']}`, does not have the `Medium Upgrade`.")
                        return

                gpNeeded = charRecords['Guild Rank'] * 1000
                if gpNeeded > charRecords['GP']:
                    await channel.send(f"{charRecords['Name']} does not have the minimum {gpNeeded}gp to upgrade their guild rank.")
                    return

                guildEmbed.title = f"Ranking Up - Guild: {guildRecords['Name']}"
                guildEmbed.description = f"Are you sure you want to rank up to rank **{charRecords['Guild Rank'] + 1}**? (Cost: {gpNeeded}gp)\n\nCurrent GP: {charRecords['GP']}gp => {charRecords['GP'] - gpNeeded}gp\n\n✅ : Yes\n\n❌: Cancel"

                if guildEmbedmsg:
                    await guildEmbedmsg.edit(embed=guildEmbed)
                else:
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                await guildEmbedmsg.add_reaction('✅')
                await guildEmbedmsg.add_reaction('❌') 

                try:
                    tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck , timeout=60)
                except asyncio.TimeoutError:
                    await guildEmbedmsg.delete()
                    await channel.send(f'Guild canceled. Use `{commandPrefix}guild rankup` command and try again!')
                    return
                else:
                    await guildEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Use `{commandPrefix}guild rankup` command and try again!")
                        await guildEmbedmsg.clear_reactions()
                        return

                newGP = (charRecords['GP'] - float(gpNeeded)) 
                try:
                    playersCollection = db.players
                    guildsCollection = db.guilds
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'GP':newGP, 'Guild Rank': charRecords['Guild Rank'] + 1}})
                    guildsCollection.update_one({'Name': guildRecords['Name']}, {"$set": {'Total Reputation':guildRecords['Total Reputation'] + starsAdded, 'Reputation': guildRecords['Reputation'] + starsAdded}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    guildEmbed.description = f"{charRecords['Name']} has ranked up! Rank {charRecords['Guild Rank']} -> {charRecords['Guild Rank'] + 1}\n\n**Current gp**: {newGP}\n"
                    if guildEmbedmsg:
                        await guildEmbedmsg.edit(embed=guildEmbed)
                    else:
                        guildEmbedmsg = await channel.send(embed=guildEmbed)
                
            else:
                await channel.send(f'The guild `{guildName}` does not exist. Please try again.')
                return


    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def leave(self,ctx, charName): 
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedEmbedmsg = None

        def guildEmbedCheck(r, u):
            sameMessage = False
            if guildEmbedmsg.id == r.message.id:
                sameMessage = True
            return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            if 'Guild' not in charRecords:
                await channel.send(f"{charRecords['Name']} cannot leave a guild because they currently do not belong to any guild.")
                return

            guildEmbed.title = f"Leaving Guild: {charRecords['Guild']}"
            guildEmbed.description = f"Are you sure you want to leave **{charRecords['Guild']}**?\n\n✅ : Yes\n\n❌: Cancel"

            if guildEmbedmsg:
                await guildEmbedmsg.edit(embed=guildEmbed)
            else:
                guildEmbedmsg = await channel.send(embed=guildEmbed)
            await guildEmbedmsg.add_reaction('✅')
            await guildEmbedmsg.add_reaction('❌') 

            try:
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck , timeout=60)
            except asyncio.TimeoutError:
                await guildEmbedmsg.delete()
                await channel.send(f'Guild canceled. Use `{commandPrefix}guild leave` command and try again!')
                return
            else:
                await guildEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Use `{commandPrefix}guild leave` command and try again!")
                    await guildEmbedmsg.clear_reactions()
                    return

            await author.remove_roles(get(guild.roles, name = charRecords['Guild']), reason=f"Left guild {charRecords['Guild']}")

            try:
                playersCollection = db.players
                playersCollection.update_one({'_id': charRecords['_id']}, {"$unset": {'Guild': 1, 'Guild Rank':1}})
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
            else:
                guildEmbed.description = f"{charRecords['Name']} has left **{charRecords['Guild']}**."
                if guildEmbedmsg:
                    await guildEmbedmsg.edit(embed=guildEmbed)
                else:
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                

    # @commands.cooldown(1, 5, type=commands.BucketType.member)
    # @guild.command()
    # async def rep(self,ctx, charName, sparkleNum=1): 
    #     channel = ctx.channel
    #     author = ctx.author
    #     guild = ctx.guild
    #     guildEmbed = discord.Embed()
    #     guildEmbedEmbedmsg = None

    #     if not isinstance(sparkleNum,int):
    #             await channel.send(f"You entered `{sparkleNum}` which is not a valid number. Please try again.")
    #             return

    #     sparkleNum = int(sparkleNum)

    #     def guildEmbedCheck(r, u):
    #         sameMessage = False
    #         if guildEmbedmsg.id == r.message.id:
    #             sameMessage = True
    #         return ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

    #     charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

    #     if charRecords:
    #         if 'Guild' not in charRecords:
    #             await channel.send(f"{charRecords['Name']} cannot buy any sparkles because they currently do not belong to any guild.")
    #             return

    #         guildRecords = await checkForGuild(ctx, charRecords['Guild']) 

    #         if guildRecords['Funds'] < 6000: 
    #             await channel.send(f"{charRecords['Name']} cannot buy any sparkles because `{charRecords['Guild']}` is not officially open and still needs funding.")
    #             return

    #         gpNeeded = 0
    #         for s in range (charRecords['Reputation'], charRecords['Reputation'] + sparkleNum):
    #             if s >= 10:
    #                 gpNeeded += 500
    #             else:
    #                 gpNeeded += 100 * (s+1)
          

    #         if gpNeeded > charRecords['GP']:
    #             await channel.send(f"{charRecords['Name']} does not have `{gpNeeded}gp` to buy {sparkleNum} sparkle(s).")
    #             return

    #         newGP = charRecords['GP'] - gpNeeded
    #         sparkleTotal = charRecords['Reputation'] + sparkleNum

    #         sparkleToGuild = 0
    #         guildEmbed.description = f"Are you sure you want to buy **{sparkleNum}** :sparkles: for {gpNeeded}gp?\n{charRecords['Reputation']} :sparkles: => {sparkleTotal} :sparkles:\n\n✅ : Yes\n\n❌: Cancel"
    #         if sparkleTotal > 10:
    #             sparkleToGuild = sparkleTotal - 10
    #             sparkleTotal = 10
    #             guildEmbed.description = f"Are you sure you want to buy **{sparkleNum}** :sparkles: {gpNeeded}gp?\n\n{sparkleToGuild} :sparkles: will go to **{charRecords['Guild']}'s** bank\n\n{charRecords['Reputation']} :sparkles: => {sparkleTotal} :sparkles:\n\n✅ : Yes\n\n❌: Cancel"

    #         guildEmbed.title = f"Guild Rep: {charRecords['Guild']}"

    #         if guildEmbedmsg:
    #             await guildEmbedmsg.edit(embed=guildEmbed)
    #         else:
    #             guildEmbedmsg = await channel.send(embed=guildEmbed)
    #         await guildEmbedmsg.add_reaction('✅')
    #         await guildEmbedmsg.add_reaction('❌') 

    #         try:
    #             tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck , timeout=60)
    #         except asyncio.TimeoutError:
    #             await guildEmbedmsg.delete()
    #             await channel.send(f'Guild canceled. Use `{commandPrefix}guild rep` command and try again!')
    #             return
    #         else:
    #             await guildEmbedmsg.clear_reactions()
    #             if tReaction.emoji == '❌':
    #                 await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Use `{commandPrefix}guild rep` command and try again!")
    #                 await guildEmbedmsg.clear_reactions()
    #                 return

    #             try:
    #                 playersCollection = db.players
    #                 guildsCollection = db.guilds
    #                 playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'GP':newGP, 'Reputation': sparkleTotal}})
    #                 if sparkleToGuild > 0:
    #                     guildsCollection.update_one({'Name': charRecords['Guild']}, {"$set": {'Reputation': guildRecords['Reputation'] + sparkleToGuild}})
    #             except Exception as e:
    #                 print ('MONGO ERROR: ' + str(e))
    #                 await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try guild rep again.")
    #             else:
    #                 guildEmbed.description = f"{charRecords['Name']} now has **{sparkleTotal}** :sparkles:\n\n**Current gp**: {newGP}\n"
    #                 if sparkleToGuild > 0:
    #                     guildEmbed.description = f"{charRecords['Name']} now has **{sparkleTotal}** :sparkles:\n\n{sparkleToGuild} :sparkles: have been donated to {charRecords['Guild']}\n\n**Current gp**: {newGP}\n"
    #                 if guildEmbedmsg:
    #                     await guildEmbedmsg.edit(embed=guildEmbed)
    #                 else:
    #                     guildEmbedmsg = await channel.send(embed=guildEmbed)
                


            
def setup(bot):
    bot.add_cog(Guild(bot))
