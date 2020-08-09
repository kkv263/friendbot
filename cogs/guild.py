import discord
import asyncio
from discord.utils import get        
from discord.ext import commands
from bfunc import  numberEmojis, numberEmojisMobile, commandPrefix, checkForChar, checkForGuild, noodleRoleArray, db, traceBack, alphaEmojis

class Guild(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
       

    @commands.group(aliases=['g'])
    async def guild(self, ctx):	
        pass

    async def cog_command_error(self, ctx, error):
        msg = None

        if isinstance(error, commands.CommandNotFound):
            await ctx.channel.send(f'Sorry, the command `***{commandPrefix}{ctx.invoked_with}***` requires an additional keyword to the command or is invalid, please try again!')
            return
            
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'charName':
                msg = "You're missing your character name in the command. "
            elif error.param.name == "guildName":
                msg = "You're missing the guild name in the command. "
            elif error.param.name == "roleName":
                msg = "You're missing the @role for the guild you want to create. "
            elif error.param.name == "channelName":
                msg = "You're missing the #channel for the guild you want to create. "
            elif error.param.name == "gpName":
                msg = "You're missing the amount of gp you want to donate to the guild." 
        # elif isinstance(error, commands.UnexpectedQuoteError) or isinstance(error, commands.ExpectedClosingQuoteError) or isinstance(error, commands.InvalidEndOfQuotedStringError):
        #     msg = "There seems to be an unexpected or a missing closing quote mark somewhere, please check your format and retry the command. "
        
        # bot.py handles this, so we don't get traceback called.
        elif isinstance(error, commands.CommandOnCooldown):
            return
        if msg:
            if ctx.command.name == "info":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild info \"guild name\"```\n"
            elif ctx.command.name == "join":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild join \"character name\" \"guild name\"```\n"
            elif ctx.command.name == "leave":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild leave \"character name\"```\n"
            elif ctx.command.name == "rep":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild rep \"character name\" sparkles```\n"
            elif ctx.command.name == "create":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild create \"character name\" \"guild name\" @rolename #channelname```\n"
            elif ctx.command.name == "fund":
                msg += f"Please follow this format:\n```yaml\n{commandPrefix}guild fund \"character name\" gp \"guild name\"```\n"

            ctx.command.reset_cooldown(ctx)
            await ctx.channel.send(msg)
        else:
            ctx.command.reset_cooldown(ctx)
            await traceBack(ctx,error)

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def create(self,ctx, charName, guildName, roleName="", channelName=""):
        channel = ctx.channel
        author = ctx.author
        guildEmbed = discord.Embed()
        guildCog = self.bot.get_cog('Guild')

        guildRole = ctx.message.role_mentions
        guildChannel = ctx.message.channel_mentions

        roles = [r.name for r in ctx.author.roles]

        # Check if the user using the command has the guildmaster role
        if 'Guildmaster' not in roles:
            await channel.send(f"You do not have the Guildmaster role to use this command.")
            return 

        if guildRole == list() or guildChannel == list():
            await channel.send(f"You are missing the guild's role and/or guild channel.")
            return 
            

        #see if channel + role + guildname matchup.
        roleStr = (guildRole[0].name.lower().replace(',', '').replace('.', '').replace(' ', '').replace('-', ''))
        guildNameStr = (guildName.lower().replace(',', '').replace('.', '').replace(' ', '').replace('-', ''))
        guildChannelStr = (guildChannel[0].name.replace('-', ''))

        if guildChannelStr != guildNameStr:
            await channel.send(f"The guild: ***{guildName}*** does not match the guild channel ***{guildChannel[0].name}***. Please try the command again with the correct channel.")
            return 
        elif guildNameStr != roleStr:
            await channel.send(f"The guild: ***{guildName}*** does not match the guild role ***{guildRole[0].name}***. Please try the command again with the correct role.")
            return

        # Grab user's noodle role
        roles = author.roles
        noodleRole = None
        for r in roles:
            if r.name in noodleRoleArray and r.name != 'Good Noodle':
                noodleRole = r

        if noodleRole:
            usersCollection = db.users
            userRecords = usersCollection.find_one({"User ID": str(author.id)})
            if userRecords: 
                charDict, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)
                if charDict:

                    # GP needed to fund guild.
                    gpNeeded = 0

                    if charDict['Level'] < 5:
                        gpNeeded = 200
                    elif charDict['Level'] < 11:
                        gpNeeded = 400
                    elif charDict['Level'] < 17:
                        gpNeeded = 600
                    elif charDict['Level'] < 21:
                        gpNeeded = 800

                    if gpNeeded > charDict['GP']:
                        await channel.send(f"***{charDict['Name']}*** does not have at least {gpNeeded} gp in order to fund ***{guildName}***.")
                        return

                    charDict['GP'] -= gpNeeded

                    noodleRep = ["Elite Noodle (0)", "True Noodle (10)", "Ascended Noodle (20)", "Immortal Noodle (30)"]
                    charID = charDict['_id']
                    if 'Guilds' not in userRecords: 
                        userRecords['Guilds'] = []

                    if 'Guild' in charDict:
                        await channel.send(f"***{charDict['Name']}*** is already a part of ***{charDict['Guild']}*** and won't be able to create another guild.")
                        return

                    # Available Noodle Roles.
                    for i in range (noodleRoleArray.index(noodleRole.name) + 1, len(noodleRoleArray)):
                        del noodleRep[-1]

                    # Look through Noodles and filter used noodles for base rep.
                    for n in userRecords["Guilds"]:
                        if n in noodleRep:
                            noodleRep.remove(n)

                    if noodleRep == list():
                        await channel.send(f"You can't create any more guilds because you have already used all of your Noodle roles to create guilds! Gain a new Noodle role if you want to create another guild!")
                        return

                    noodleRepStr = ""
                    for i in range(0, len(noodleRep)):
                        noodleRepStr += f"{alphaEmojis[i]}: {noodleRep[i]}\n"

                    def guildNoodleEmbedcheck(r, u):
                        sameMessage = False
                        if guildEmbedmsg.id == r.message.id:
                            sameMessage = True
                        return (r.emoji in alphaEmojis[:len(noodleRep)] or (str(r.emoji) == '❌')) and u == author and sameMessage


                    guildEmbed.add_field(name=f"Choose the Noodle role which you would like to use to create this guild. This will affect the amount of reputation which the guild starts with.", value=noodleRepStr, inline=False)
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                    await guildEmbedmsg.add_reaction('❌')

                    try:
                        tReaction, tUser = await self.bot.wait_for("reaction_add", check=guildNoodleEmbedcheck, timeout=60)
                    except asyncio.TimeoutError:
                        await guildEmbedmsg.delete()
                        await channel.send('Guild command timed out! Try using the command again.')
                        ctx.command.reset_cooldown(ctx)
                        return
                    else:
                        if tReaction.emoji == '❌':
                            await guildEmbedmsg.edit(embed=None, content=f"Guild command canceled. Please use the command and try again!")
                            await guildEmbedmsg.clear_reactions()
                            ctx.command.reset_cooldown(ctx)
                            return
                    guildEmbed.clear_fields()
                    await guildEmbedmsg.clear_reactions()
                    baseRep = int(noodleRep[alphaEmojis.index(tReaction.emoji[0])].split(' (')[1].replace(')',""))
                    userRecords['Guilds'].append(noodleRep[alphaEmojis.index(tReaction.emoji[0])])

                    # Quick check to see if guild already exists
                    guildsCollection = db.guilds
                    guildExists = guildsCollection.find_one({"Name": {"$regex": guildName, '$options': 'i' }})


                    if guildExists:
                        await channel.send(f"There is already a guild by the name of ***{guildName}***. Please try creating a guild with a different name.")
                        return

                    guildsDict = {'Role ID': str(guildRole[0].id), 'Channel ID': str(guildChannel[0].id), 'Name': guildName, 'Funds': gpNeeded, 'Guildmaster': charDict['Name'], 'Guildmaster ID': str(author.id), 'Reputation': baseRep, 'Total Reputation': baseRep}
                    await author.add_roles(guildRole[0], reason=f"Created guild {guildName}")

                    try:
                        playersCollection = db.players
                        playersCollection.update_one({'_id': charID}, {"$set": {"Guild": guildName, 'Guild Rank': 1, 'GP':charDict['GP']}})
                        usersCollection.update_one({"User ID": str(author.id)}, {"$set": {"Guilds": userRecords['Guilds']}})
                        guildsCollection.insert_one(guildsDict)
                    except Exception as e:
                        print ('MONGO ERROR: ' + str(e))
                        guildEmbedmsg = await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try creating your guild again.")
                    else:
                        print('Success')

                        guildEmbed.title = f"Guild Creation: {guildName}"
                        guildEmbed.description = f"***{charDict['Name']}*** has created ***{guildName}***!\n\n6000 gp must be donated in order for the guild to officially open!\n\nAny character who is not in a guild can fund this guild using the following command:\n```yaml\n{commandPrefix}guild fund \"character name\" gp \"{guildName}\"```\nThe guild's status can be checked using the following command:\n```yaml\n{commandPrefix}guild info \"{guildName}\"```\nCurrent Guild Funds: {gpNeeded} gp"
                        if guildEmbedmsg:
                            await guildEmbedmsg.clear_reactions()
                            await guildEmbedmsg.edit(embed=guildEmbed)
                        else: 
                            guildEmbedmsg = await channel.send(embed=guildEmbed)
                          
            else:
                await channel.send(f'***{author.display_name}*** you will need to play at least one game with a character before you can create a guild.')
                return

        else:
            await channel.send(f'***{author.display_name}***, you need the ***Elite Noodle*** role or higher to create a guild. ')
            return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def info(self,ctx, guildName): 
        channel = ctx.channel
        author = ctx.author
        guild = ctx.guild
        guildEmbed = discord.Embed()
        guildEmbedmsg = None

        guildRecords, guildEmbedmsg = await checkForGuild(ctx,guildName, guildEmbed) 

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

            guildEmbed.title = f"{guildRecords['Name']}: {guildRank}" 
            # Does not list Guildmaster
            # guildEmbed.add_field (name= 'Guildmaster', value=f"{guild.get_member(int(guildRecords['Guildmaster ID'])).mention} **{guildRecords['Guildmaster']}**\n", inline=False)

            playersCollection = db.players
            guildMembers = list(playersCollection.find({"Guild": guildRecords['Name']}))

            if guildMembers != list():
                guildMemberStr = ""
                for g in guildMembers:
                    guildMemberStr += f"{guild.get_member(int(g['User ID'])).mention} **{g['Name']}** [Rank {g['Guild Rank']}]\n"
                guildEmbed.add_field(name="Members", value=guildMemberStr)
            else:
                guildEmbed.add_field(name="Members", value="There are no guild members currently.")

            if guildRecords['Funds'] < 6000:
                guildEmbed.add_field(name="Funds", value=f"{guildRecords['Funds']} gp / 6000 gp.\n**{6000 - guildRecords['Funds']} gp** required to open the guild!", inline=False)
            else:
                guildEmbed.add_field(name="Reputation", value=f"Total Reputation: {guildRecords['Total Reputation']} :sparkles:\nBank: {guildRecords['Reputation']} :sparkles:", inline=False)


            await channel.send(embed=guildEmbed)

        else:
            await channel.send(f'The guild ***{guildName}*** does not exist. Please try again.')
            return

    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command(aliases=['join'])
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
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            guildRecords, guildEmbedmsg = await checkForGuild(ctx,guildName,guildEmbed) 

            if guildRecords:
                # if guildRecords['Funds'] >= 6000:
                #     await channel.send(f"***{guildRecords['Name']}*** is not expecting any funds. This guild has already been opened.")
                #     return

                if 'Guild' in charRecords:
                    if charRecords['Guild'] != guildRecords['Name']:
                        await channel.send(f"***{charRecords['Name']}*** cannot fund ***{guildRecords['Name']}*** because they belong to ***{charRecords['Guild']}***.")
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
                    await channel.send(f"***{charRecords['Name']}*** currently has {charRecords['GP']} gp and does not have {gpFund} gp in order to fund ***{guildRecords['Name']}***.")
                    return
                     

                if gpNeeded > charRecords['GP']:
                    await channel.send(f"***{charRecords['Name']}*** does not have at least {gpNeeded} gp in order to fund ***{guildRecords['Name']}***.")
                    return

                if gpNeeded > float(gpFund):
                    await channel.send(f"***{charRecords['Name']}*** needs to donate at least {gpNeeded} gp in order to fund ***{guildRecords['Name']}***.")
                    return

                        
                guildEmbed.title = f"Fund Guild: {guildRecords['Name']}"
                guildEmbed.description = f"Are you sure you want to fund ***{guildRecords['Name']}***?\n:warning: ***{charRecords['Name']}* will automatically join *{guildRecords['Name']}* after funding the guild.**\n\n✅: Yes\n\n❌: Cancel"


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
                    await channel.send(f'Guild canceled. Try again using the following command:\n```yaml\n{commandPrefix}guild join```')
                    return
                else:
                    await guildEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await guildEmbedmsg.edit(embed=None, content=f"Shop canceled. Try again using the following command:\n```yaml\n{commandPrefix}tp buy```")
                        await guildEmbedmsg.clear_reactions()
                        return

                oldFundGP = guildRecords['Funds']
                guildRecords['Funds'] += float(gpFund) 

                if  guildRecords['Funds'] + gpNeeded >= 6000  and oldFundGP < 6000:
                    refundGP = guildRecords['Funds'] - (6000 + gpNeeded)

                newGP = (charRecords['GP'] - float(gpFund)) + refundGP
                await author.add_roles(guild.get_role(int(guildRecords['Role ID'])), reason=f"Funded guild {guildRecords['Name']}")


                try:
                    playersCollection = db.players
                    guildsCollection = db.guilds
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'Guild': guildRecords['Name'], 'GP':newGP, 'Guild Rank': 1}})
                    if oldFundGP < 6000:
                        guildsCollection.update_one({'Name': guildRecords['Name']}, {"$set": {'Funds':guildRecords['Funds']}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try guild join again.")
                else:
                    guildEmbed.title = f"Fund Guild: {guildRecords['Name']}"
                    guildEmbed.description = f"***{charRecords['Name']}*** has joined ***{guildRecords['Name']}***\n\n**Current gp**: {newGP}\n"
                    if guildRecords['Funds'] < 6000:
                        guildEmbed.description = f"***{charRecords['Name']}*** has funded ***{guildRecords['Name']}*** with {gpFund} gp.\nIf this amount puts the guild's funds over 6000 gp, the leftover is given back to the character.\n\n**Current Guild Funds**: {guildRecords['Funds']} gp / 6000 gp\n\n**Current gp**: {newGP}\n"
                    elif guildRecords['Funds'] >= 6000 and oldFundGP < 6000:
                        guildEmbed.description = f"***{charRecords['Name']}*** has joined ***{guildRecords['Name']}***\n\n**Current gp**: {newGP}\n"
                        guildEmbed.description += f"Congratulations! :tada: ***{guildRecords['Name']}***  is officially open!"
                    else:
                        guildEmbed.description = f"***{charRecords['Name']}*** has joined ***{guildRecords['Name']}***\n\n**Current gp**: {newGP}\n"

                    if guildEmbedmsg:
                        await guildEmbedmsg.edit(embed=guildEmbed)
                    else:
                        guildEmbedmsg = await channel.send(embed=guildEmbed)

            else:
                await channel.send(f'The guild ***{guildName}*** does not exist. Please try again.')
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
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            if 'Guild' not in charRecords:
                await channel.send(f"***{charRecords['Name']}*** cannot upgrade their guild rank because they currently do not belong to a guild.")
                return

            guildRecords, guildEmbedmsg = await checkForGuild(ctx,charRecords['Guild'],guildEmbed) 
            
            if guildRecords:

                if guildRecords['Funds'] < 6000: 
                    await channel.send(f"***{charRecords['Name']}*** cannot upgrade their guild rank because ***{charRecords['Guild']}*** is not officially open and still needs funding.")
                    return

                if charRecords['Guild Rank'] > 3:
                    await channel.send(f"***{charRecords['Name']}*** is already at the max rank and does not need to upgrade anymore.")
                    return

                elif charRecords['Guild Rank'] == 3:
                    if guildRecords['Total Reputation'] < 60:
                        await channel.send(f"***{charRecords['Name']}*** cannot upgrade their rank because their guild ***{guildRecords['Name']}*** has not unlocked their Masterwork upgrade yet.")
                        return
                elif charRecords['Guild Rank'] == 2:
                    if guildRecords['Total Reputation'] < 30:
                        await channel.send(f"***{charRecords['Name']}*** cannot upgrade their rank because their guild ***{guildRecords['Name']}*** has not unlocked their Large upgrade yet.")
                        return
                elif charRecords['Guild Rank'] == 1:
                    if guildRecords['Total Reputation'] < 10:
                        await channel.send(f"***{charRecords['Name']}*** cannot upgrade their rank because their guild ***{guildRecords['Name']}*** has not unlocked their Medium upgrade yet.")
                        return

                gpNeeded = charRecords['Guild Rank'] * 1000
                if gpNeeded > charRecords['GP']:
                    await channel.send(f"***{charRecords['Name']}*** does not have {gpNeeded} gp in order to upgrade their guild rank.")
                    return

                guildEmbed.title = f"Ranking Up - Guild: {guildRecords['Name']}"
                guildEmbed.description = f"Are you sure you want to upgrade your rank to **{charRecords['Guild Rank'] + 1}**? (Cost: {gpNeeded} gp)\n\nCurrent gp: {charRecords['GP']} gp → {charRecords['GP'] - gpNeeded} gp\n\n✅: Yes\n\n❌: Cancel"

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
                    await channel.send(f'Guild canceled. Try again using the following command:\n```yaml\n{commandPrefix}guild rankup```')
                    return
                else:
                    await guildEmbedmsg.clear_reactions()
                    if tReaction.emoji == '❌':
                        await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Try again using the following command:\n```yaml\n{commandPrefix}guild rankup```")
                        await guildEmbedmsg.clear_reactions()
                        return

                newGP = (charRecords['GP'] - float(gpNeeded)) 
                try:
                    playersCollection = db.players
                    playersCollection.update_one({'_id': charRecords['_id']}, {"$set": {'GP':newGP, 'Guild Rank': charRecords['Guild Rank'] + 1}})
                except Exception as e:
                    print ('MONGO ERROR: ' + str(e))
                    await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
                else:
                    guildEmbed.description = f"***{charRecords['Name']}*** has ranked up! Rank **{charRecords['Guild Rank']}** → **{charRecords['Guild Rank'] + 1}**\n\n**Current gp**: {newGP}\n"
                    if guildEmbedmsg:
                        await guildEmbedmsg.edit(embed=guildEmbed)
                    else:
                        guildEmbedmsg = await channel.send(embed=guildEmbed)
                
            else:
                await channel.send(f'The guild ***{guildName}*** does not exist. Please try again.')
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
            return sameMessage and ((str(r.emoji) == '✅') or (str(r.emoji) == '❌')) and u == author

        charRecords, guildEmbedmsg = await checkForChar(ctx, charName, guildEmbed)

        if charRecords:
            if 'Guild' not in charRecords:
                await channel.send(f"***{charRecords['Name']}*** cannot leave a guild because they currently do not belong to any guild.")
                return

            guildEmbed.title = f"Leaving Guild: {charRecords['Guild']}"
            guildEmbed.description = f"Are you sure you want to leave ***{charRecords['Guild']}***?\n\n✅: Yes\n\n❌: Cancel"

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
                await channel.send(f'Guild canceled. Try again using the following command:\n```yaml\n{commandPrefix}guild leave```')
                return
            else:
                await guildEmbedmsg.clear_reactions()
                if tReaction.emoji == '❌':
                    await guildEmbedmsg.edit(embed=None, content=f"Guild canceled. Try again using the following command:\n```yaml\n{commandPrefix}guild leave```")
                    await guildEmbedmsg.clear_reactions()
                    return

            playersCollection = db.players
            guildAmount = list(playersCollection.find({"User ID": str(author.id), "Guild": {"$regex": charRecords['Guild'], '$options': 'i' }}))
            # If there is only one of user's character in the guild remove the role.
            if (len(guildAmount) == 1):
                await author.remove_roles(get(guild.roles, name = charRecords['Guild']), reason=f"Left guild {charRecords['Guild']}")

            try:
                playersCollection.update_one({'_id': charRecords['_id']}, {"$unset": {'Guild': 1, 'Guild Rank':1}})
            except Exception as e:
                print ('MONGO ERROR: ' + str(e))
                await channel.send(embed=None, content="Uh oh, looks like something went wrong. Please try shop buy again.")
            else:
                guildEmbed.description = f"***{charRecords['Name']}*** has left ***{charRecords['Guild']}***."
                if guildEmbedmsg:
                    await guildEmbedmsg.edit(embed=guildEmbed)
                else:
                    guildEmbedmsg = await channel.send(embed=guildEmbed)
                
def setup(bot):
    bot.add_cog(Guild(bot))
