import discord
import asyncio
from discord.utils import get        
from discord.ext import commands
from bfunc import  numberEmojis, commandPrefix

class Guild(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
       
    async def guildsList(self, ctx, member):
        def guildEmbedCheck(r, u):
                return (r.emoji in numberEmojis[:g + 1] or str(r.emoji) == '❌') and u == author

        guild = ctx.guild
        # Channel where guildsMsg is stored
        channel = self.bot.get_channel(579858636646383626) 
        author = ctx.author
        # Message where guilds are stored.
        guildsMsg = await channel.fetch_message(579859120321200138)
        guildMember = guild.get_member_named(member)
        commandName = ctx.command.name

        if guildMember is None:
            await ctx.channel.send(content=f"The user {member} is not valid. Make sure the user follows the 'User#1234' format (case-sensitive) and try the command again.")
            return

        for char in '@&<>':
            guildsMsg.content = guildsMsg.content.replace(char,"")

        if author.mentioned_in(guildsMsg):
            guildsList = guildsMsg.content.split(str(author.id) + ' - ',1)[1].split('\n',1)[0].split(',') 
            guildsList = list(map(int, guildsList))
            guildsRolesList = []
        else:
            return

        guildEmbed = discord.Embed()
        guildString = ""

        for x in range(0,len(guildsList)):
            guildsRolesList.append(get(guild.roles, id=guildsList[x]))
        
        for g in range(0, len(guildsList)):
            guildString = guildString + numberEmojis[g] + ": " + guildsRolesList[g].name + "\n"

        guildEmbed.add_field(name=f"Which guild would you like to {commandName} {member}? \nReact with one of the numbers below.", value=guildString, inline=False)
        guildEmbed.set_footer(text= "React with ❌ to cancel")

        try:
            guildAddMsg = await ctx.channel.send(embed = guildEmbed)
            await guildAddMsg.add_reaction('❌')
            gReaction, gUser = await self.bot.wait_for("reaction_add", check=guildEmbedCheck, timeout=60)
        except asyncio.TimeoutError:
            await guildAddMsg.delete()
            await ctx.channel.send(f'Guild {commandName} command timed out!')
            return
        else:
            if gReaction.emoji == '❌':
                  await guildAddMsg.edit(embed=None, content=f"Guild {commandName} command canceled.")
                  await guildAddMsg.clear_reactions()
                  return
            
            guildRole = guildsRolesList[int(gReaction.emoji[0]) - 1]

            if commandName == "add":
                await guildMember.add_roles(guildRole, reason=f"{author} used guild command add {member} for guild {guildRole.name}")     
                await guildAddMsg.edit(embed=None, content=f"You have added {member} to guild {guildRole.name}! Please double check if necessary")
            if commandName == "remove":
                await guildMember.remove_roles(guildRole, reason=f"{author} used guild command remove {member} for guild {guildRole.name}")      
                await guildAddMsg.edit(embed=None, content=f"You have removed {member} from guild {guildRole.name}! Please double check if necessary")
            await guildAddMsg.clear_reactions()

        return

    @commands.group()
    async def guild(self, ctx):	
        pass

    @commands.has_role('Guildmaster')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def add(self,ctx,member):
        guildCog = self.bot.get_cog('Guild')
        await guildCog.guildsList(ctx,member)

    @commands.has_role('Guildmaster')
    @commands.cooldown(1, 5, type=commands.BucketType.member)
    @guild.command()
    async def remove(self,ctx,member):
        guildCog = self.bot.get_cog('Guild')
        await guildCog.guildsList(ctx,member)

def setup(bot):
    bot.add_cog(Guild(bot))
