import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands

class Misc(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot

    @commands.cooldown(1, 60, type=commands.BucketType.member)
    @commands.command()
    async def uwu(self,ctx):
        channel = ctx.channel
        vowels = ['a','e','i','o','u']
        faces = ['rawr XD', 'OwO', 'owo', 'UwU', 'uwu']
        async with channel.typing():
            async for message in channel.history(before=ctx.message, limit=1, oldest_first=False):
                uwuMessage = message.content.replace('r', 'w')
                uwuMessage = uwuMessage.replace('l', 'w')
                uwuMessage = uwuMessage.replace('ove', 'uv')
                uwuMessage = uwuMessage.replace('.', '!')
                uwuMessage = uwuMessage.replace(' th', ' d')
                uwuMessage = uwuMessage.replace('th', 'f')
                uwuMessage = uwuMessage.replace('mom', 'yeshh')

                for v in vowels:
                  uwuMessage = uwuMessage.replace('n'+ v, 'ny'+v)

        i = 0
        while i < len(uwuMessage):
            if uwuMessage[i] == '!':
                randomFace = random.choice(faces)
                if i == len(uwuMessage):
                    uwuMessage = uwuMessage + ' ' + randomFace
                    break
                else:
                  uwuList = list(uwuMessage)
                  uwuList.insert(i+1, " " + randomFace)
                  uwuMessage = ''.join(uwuList)
                  i += len(randomFace)
            i += 1
            

        await channel.send(content=message.author.display_name + ":\n" +  uwuMessage)
        await ctx.message.delete()
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,payload):
        tMessage = 650482015342166036
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id == tMessage:
            if payload.emoji.name == "1️⃣":
                name = 'Tier 1' 
                role = get(guild.roles, name = name)
                validRoles = ['Junior Friend', 'Journey Friend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "2️⃣":
                name = 'Tier 2' 
                role = get(guild.roles, name = name)
                validRoles = ['Journey Friend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "3️⃣":
                name = 'Tier 3' 
                role = get(guild.roles, name = name)
                validRoles = ['Elite Friend', 'True Friend']
            elif payload.emoji.name == "4️⃣":
                name = 'Tier 4' 
                role = get(guild.roles, name = name)
                validRoles = ['True Friend']
            else:
                role = None

            if role is not None:
                member = guild.get_member(payload.user_id)
                if member is not None:
                    roles = [r.name for r in member.roles]
                    channel = guild.get_channel(payload.channel_id)
                    if any(role in roles for role in validRoles):
                        await member.remove_roles(role)
                        successMsg = await channel.send(f":tada: {member.display_name}, I have removed the role `{name}`. You will no longer be notified for these type of games through pings.")
                        await asyncio.sleep(15) 
                        await successMsg.delete()

                else:
                    print('member not found')
            else:
                print('role not found')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self,payload):
        tMessage = 650482015342166036
        guild = self.bot.get_guild(payload.guild_id)
        validRoles = []

        if payload.message_id == tMessage:
            if payload.emoji.name == "1️⃣":
                name = 'Tier 1' 
                role = get(guild.roles, name = name)
                validRoles = ['Junior Friend', 'Journey Friend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "2️⃣":
                name = 'Tier 2' 
                role = get(guild.roles, name = name)
                validRoles = ['Journey Friend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "3️⃣":
                name = 'Tier 3' 
                role = get(guild.roles, name = name)
                validRoles = ['Elite Friend', 'True Friend']
            elif payload.emoji.name == "4️⃣":
                name = 'Tier 4' 
                role = get(guild.roles, name = name)
                validRoles = ['True Friend']
            else:
                role = None

            if role is not None:
                member = guild.get_member(payload.user_id)

                if member is not None:
                    roles = [r.name for r in member.roles]
                    channel = guild.get_channel(payload.channel_id)

                    if any(role in roles for role in validRoles):    
                        await member.add_roles(role)
                        successMsg = await channel.send(f":tada: {member.display_name}, I have added the role `{name}`. You will be notified for these type of games through pings.")
                        await asyncio.sleep(15) 
                        await successMsg.delete()
                    else:
                        channel = guild.get_channel(payload.channel_id)
                        errorMsg = await channel.send(f"❗ {member.display_name}, You can't add the role `{name}` because you don't have the the required roles! - ({', '.join(validRoles)})")
                        originalMessage = await channel.fetch_message(tMessage)
                        await originalMessage.remove_reaction(payload.emoji,member)
                        await asyncio.sleep(15) 
                        await errorMsg.delete()

                        
                else:
                    print('member not found')
            else:
                print('role not found')
            

    @commands.Cog.listener()
    async def on_message(self,msg):
        if any(word in msg.content.lower() for word in ['thank', 'thank you', 'thx', 'gracias']) and 'bot friend' in msg.content.lower():
            await msg.add_reaction('❤️')
            await msg.channel.send("You're welcome friend!")
            
        
def setup(bot):
    bot.add_cog(Misc(bot))
