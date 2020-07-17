import discord
import asyncio
from discord.utils import get        
from discord.ext import commands
from bfunc import  numberEmojis, numberEmojisMobile, commandPrefix

class Campaign(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
       
    async def campaignsList(self, ctx, member):
        def campaignEmbedCheck(r, u):
            sameMessage = False
            if campaignAddMsg.id == r.message.id:
                sameMessage = True
            return (r.emoji in numberEmojis[:g + 1] or r.emoji in numberEmojisMobile[:g + 1] or str(r.emoji) == '❌') and u == author and sameMessage

        guild = ctx.guild
        # Channel where campaignMsg is stored
        channel = self.bot.get_channel(597572722654052352) #728476108940640297 597572722654052352
        author = ctx.author
        # Message where campaigns are stored.
        campaignMsg = await channel.fetch_message(729430390598664193) #729127829362442290 729430390598664193
        print(campaignMsg)
        campaignMember = guild.get_member_named(member)
        commandName = ctx.command.name

        if campaignMember is None:
            await ctx.channel.send(content=f"The user {member} is not valid. Make sure the user follows the 'User#1234' format (case-sensitive) and try the command again.")
            return
        memberRoles = [x.name for x in campaignMember.roles]
        if "D&D Friend" not in memberRoles and "Campaign Friend" not in memberRoles:
            await ctx.channel.send(content=f"The user {member} is not valid. They need to have applied to the server.")
            return

        for char in '@&<>':
            campaignMsg.content = campaignMsg.content.replace(char,"")

        if author.mentioned_in(campaignMsg):
            campaignsList = campaignMsg.content.split(str(author.id) + ' - ',1)[1].split('\n',1)[0].split(',') 
            print(campaignsList)
            campaignsList = list(map(int, campaignsList))
            campaignRolesList = []
        else:
            return 

        campaignEmbed = discord.Embed()
        campaignString = ""

        for x in range(0,len(campaignsList)):
            campaignRolesList.append(get(guild.roles, id=campaignsList[x]))
        
        for g in range(0, len(campaignsList)):
            campaignString = campaignString + numberEmojis[g] + ": " + campaignRolesList[g].name + "\n"

        campaignEmbed.add_field(name=f"Which campaign would you like to {commandName} {member}? \nReact with one of the numbers below.", value=campaignString, inline=False)
        campaignEmbed.set_footer(text= "React with ❌ to cancel")

        try:
            campaignAddMsg = await ctx.channel.send(embed = campaignEmbed)
            await campaignAddMsg.add_reaction('❌')
            for g in range(0, len(campaignsList)):
                await campaignAddMsg.add_reaction(numberEmojis[g])
            gReaction, gUser = await self.bot.wait_for("reaction_add", check=campaignEmbedCheck, timeout=60)
        except asyncio.TimeoutError:
            await campaignAddMsg.delete()
            await ctx.channel.send(f'Campaign {commandName} command timed out!')
            return
        else:
            if gReaction.emoji == '❌':
                  await campaignAddMsg.edit(embed=None, content=f"Campaign {commandName} command canceled.")
                  await campaignAddMsg.clear_reactions()
                  return
            
            campaignRole = campaignRolesList[int(gReaction.emoji[0]) - 1]

            if commandName == "add":
                await campaignMember.add_roles(campaignRole, reason=f"{author} used campaign command add {member} for campaign {campaignRole.name}")     
                await campaignAddMsg.edit(embed=None, content=f"You have added {member} to campaign {campaignRole.name}! Please double check if necessary.")
            if commandName == "remove":
                await campaignMember.remove_roles(campaignRole, reason=f"{author} used campaign command remove {member} for campaign {campaignRole.name}")      
                await campaignAddMsg.edit(embed=None, content=f"You have removed {member} from campaign {campaignRole.name}! Please double check if necessary.")
            await campaignAddMsg.clear_reactions()

        return

    @commands.group()
    async def campaign(self, ctx):	
        pass

    @commands.has_role('Campaign Master')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @campaign.command()
    async def add(self,ctx, *, member):
        campaignCog = self.bot.get_cog('Campaign')
        await campaignCog.campaignsList(ctx,member)

    @commands.has_role('Campaign Master')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @campaign.command()
    async def remove(self,ctx, *, member):
        campaignCog = self.bot.get_cog('Campaign')
        await campaignCog.campaignsList(ctx,member)

def setup(bot):
    bot.add_cog(Campaign(bot))
