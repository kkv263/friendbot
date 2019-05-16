import discord
import asyncio
from datetime import datetime,timedelta
from discord.utils import get        
from discord.ext import commands
from bfunc import roleArray, calculateTreasure, timeConversion 

class Apps(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def app(self, ctx):	
        pass
      
    @app.command()
    @commands.has_any_role('Mod Friend', 'Admins')
    async def edit(self, ctx, num, *, editString=""):
        # The Bot
        botUser = self.bot.get_user(566024681824452619)
        # App Logs channel 
        channel = self.bot.get_channel(388591318814949376) 

        msgFound = False
        async with channel.typing():
            async for message in channel.history(oldest_first=False):
                if int(num) == message.id and message.author == botUser:
                    editMessage = message
                    msgFound = True
                    break 

        if not msgFound:
            delMessage = await ctx.channel.send(content=f"I couldn't find message - {num}. Please try again, I will delete your message and this message in 10 seconds")
            await asyncio.sleep(10) 
            await delMessage.delete()
            await ctx.message.delete() 
            return

        await editMessage.edit(content=editString embed=None)
        delMessage = await ctx.channel.send(content=f"I have edited the message {num}.\n```{editString}```\nPlease double check that the edit is correct. I will now delete your message and this message in 30 seconds")
        await asyncio.sleep(30) 
        await delMessage.delete()
        await ctx.message.delete() 

    @commands.Cog.listener()
    async def on_message(self,msg):
        def msgCheck(r, u):
            sameMessage = False
            if botMsg.id == r.message.id:
                sameMessage = True

            return ((str(r.emoji) == '✅' or str(r.emoji) == '❌' or str(r.emoji) == '🚼') and sameMessage and u.name != "Bot Friend")

        # appchannel
        channel = self.bot.get_channel(388591318814949376)
        guild = msg.guild
        if channel and channel.id == 388591318814949376 and msg.author.name == 'Application Bot Friend':
            botMsg = await channel.send(embed=msg.embeds[0])
            await msg.delete()
            await botMsg.add_reaction('✅')
            await botMsg.add_reaction('❌')
            await botMsg.add_reaction('🚼')

            mReaction, mUser = await self.bot.wait_for("reaction_add", check=msgCheck)

            appDict = botMsg.embeds[0].to_dict()
            appNum = appDict['title'].split('#')[1] 
            appDiscord = appDict['fields'][0]['value']
            appHash = appDiscord.split('#')[1]
            appAge = appDict['fields'][1]['value']
            appMember = guild.get_member_named(appDiscord)

            if mReaction.emoji == '✅':
                # Session Channel
                sessionChannel = self.bot.get_channel(382045698931294208)
                await botMsg.edit(embed=None, content=f"{appNum}. {appMember.mention} #{appHash}")
                await botMsg.clear_reactions()

                if int(appAge) < 18:
                    kidRole = get(guild.roles, name = 'Under-18 Friendling')
                    await appMember.add_roles(kidRole, reason="Approved Application, the user is under 18")
                
                limit = 100
                playedGame = False
                async for message in sessionChannel.history(limit=limit, oldest_first=False):
                    if appMember.mentioned_in(message):
                        playedGame = True
                        juniorRole = get(guild.roles, name = 'Junior Friend')
                        await appMember.add_roles(juniorRole, reason=f"Approved Application, the user has played at least one game. I have checked in the last {limit} session-logs")
                        break

                if not playedGame:
                    newRole = get(guild.roles, name = 'New Friend')
                    await appMember.add_roles(newRole, reason=f"Approved Application, The user has not played at least one game. I have checked in the last {limit} session-logs")
                
                unregRole = get(guild.roles, name = 'Unregistered Friend')
                await appMember.remove_roles(unregRole)

                await appMember.send(f"Hello, {appMember.name}.\n\nThank you for applying to D&D Friends! The D&D Friends Mod team has approved your application and you have been assigned the appropriate roles.\n\nIf you have any further questions then please don't hesitate to ask in our #help-for-players channel or message a Mod Friend!")

            elif mReaction.emoji == '❌':
                await botMsg.edit(embed=None, content=f"{appNum}. {guild.get_member_named(appDiscord).mention} #{appHash} [DENIED - Under 18 and not ok with explicit/adult content]")
                await botMsg.clear_reactions()
                await appMember.send(f"Hello, {appMember.name}.\n\nThank you for applying to D&D Friends! Unfortunately, the D&D Friends Mod team has declined your application since we do not allow members under 18 years of age who are not fine with explicit/adult content (and answered 'No' on the application form). If you have any questions or inquiries, please direct them to our Reddit or Twitter accounts:\nReddit - <https://www.reddit.com/user/DnDFriends/>\nTwitter - <https://twitter.com/DnD_Friends>\n\nWe hope you find other like-minded people to play D&D with. Good luck!")
             
            elif mReaction.emoji == '🚼':
                await botMsg.edit(embed=None, content=f"{appNum}. {guild.get_member_named(appDiscord).mention} #{appHash} [DENIED - Under 15]")
                await botMsg.clear_reactions()
                await appMember.send(f"Hello, {appMember.name}.\n\nThank you for applying to D&D Friends! Unfortunately, the D&D Friends Mod team has declined your application since you did not meet the cut-off age. If you have any questions or inquiries, please direct them to our Reddit or Twitter accounts:\nReddit - <https://www.reddit.com/user/DnDFriends/>\nTwitter - <https://twitter.com/DnD_Friends>\n\nWe hope you find other like-minded people to play D&D with. Good luck!")
                

def setup(bot):
    bot.add_cog(Apps(bot))
