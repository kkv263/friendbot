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
    async def on_raw_reaction_add(self,payload):
        # Message for reaction
        tMessage = 658423423592169556
        guild = self.bot.get_guild(payload.guild_id)

        if payload.message_id == tMessage:
            if payload.emoji.name == "1️⃣" or payload.emoji.name == '1⃣':
                name = 'Tier 1' 
                role = get(guild.roles, name = name)
                validRoles = ['Junior Friend', 'Journeyfriend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "2️⃣" or payload.emoji.name == '2⃣':
                name = 'Tier 2' 
                role = get(guild.roles, name = name)
                validRoles = ['Journeyfriend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "3️⃣" or payload.emoji.name == '3⃣':
                name = 'Tier 3' 
                role = get(guild.roles, name = name)
                validRoles = ['Elite Friend', 'True Friend']
            elif payload.emoji.name == "4️⃣" or payload.emoji.name == '4⃣':
                name = 'Tier 4' 
                role = get(guild.roles, name = name)
                validRoles = ['True Friend']
            #this will allow everybody to readd their T0 role, but that should not hurt anyone
            #by creating an additional check to limit to people that only have these roles that could be fixed
            #but I don't quite see the reason to do so
            elif payload.emoji.name == "0️⃣" or payload.emoji.name == '0⃣':
                name = 'Tier 0' 
                role = get(guild.roles, name = name)
                validRoles = ['D&D Friend']
            else:
                role = None

            if role is not None:
                member = guild.get_member(payload.user_id)
                if member is not None:
                    roles = [r.name for r in member.roles]
                    channel = guild.get_channel(payload.channel_id)
                    if any(role in roles for role in validRoles):
                        await member.remove_roles(role)
                        successMsg = await member.send(f"D&D Friends: :tada: {member.display_name}, I have removed the role `{name}`. You will no longer be notified for these type of games through pings.")
                        await asyncio.sleep(15) 
                    else:
                        channel = guild.get_channel(payload.channel_id)
                        errorMsg = await member.send(f"D&D Friends: ❗ {member.display_name}, You can't remove the role `{name}` because you don't have the the required roles! - ({', '.join(validRoles)})")
                        originalMessage = await channel.fetch_message(tMessage)
                        await originalMessage.remove_reaction(payload.emoji,member)
                        await asyncio.sleep(15) 

                else:
                    print('member not found')
            else:
                print('role not found')

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self,payload):
        # Message for reaction
        tMessage = 658423423592169556

        guild = self.bot.get_guild(payload.guild_id)
        validRoles = []

        if payload.message_id == tMessage:
            if payload.emoji.name == "1️⃣" or payload.emoji.name == '1⃣':
                name = 'Tier 1' 
                role = get(guild.roles, name = name)
                validRoles = ['Junior Friend', 'Journeyfriend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "2️⃣" or payload.emoji.name == '2⃣':
                name = 'Tier 2' 
                role = get(guild.roles, name = name)
                validRoles = ['Journeyfriend', 'Elite Friend', 'True Friend']
            elif payload.emoji.name == "3️⃣" or payload.emoji.name == '3⃣':
                name = 'Tier 3' 
                role = get(guild.roles, name = name)
                validRoles = ['Elite Friend', 'True Friend']
            elif payload.emoji.name == "4️⃣" or payload.emoji.name == '4⃣':
                name = 'Tier 4' 
                role = get(guild.roles, name = name)
                validRoles = ['True Friend']
            #this will allow everybody to readd their T0 role, but that should not hurt anyone
            #by creating an additional check to limit to people that only have these roles that could be fixed
            #but I don't quite see the reason to do so
            elif payload.emoji.name == "0️⃣" or payload.emoji.name == '0⃣':
                name = 'Tier 0' 
                role = get(guild.roles, name = name)
                validRoles = ['D&D Friend']
            else:
                role = None

            if role is not None:
                member = guild.get_member(payload.user_id)

                if member is not None:
                    roles = [r.name for r in member.roles]
                    channel = guild.get_channel(payload.channel_id)

                    if any(role in roles for role in validRoles):    
                        await member.add_roles(role)
                        successMsg = await member.send(f"D&D Friends: :tada: {member.display_name}, I have added the role `{name}`. You will be notified for these type of games through pings.")
                        await asyncio.sleep(15) 
                        
                else:
                    print('member not found')
            else:
                print('role not found')
            

    @commands.Cog.listener()
    async def on_message(self,msg):
        if any(word in msg.content.lower() for word in ['thank', 'thank you', 'thx', 'gracias']) and 'bot friend' in msg.content.lower():
            await msg.add_reaction('❤️')
            await msg.channel.send("You're welcome friend!")
        #add wave emoji to join messages
        if(msg.type.value == 7):
            await msg.add_reaction('👋')
        # suggestions :)
        # sChannelID = 624410169396166656 

        # voting channel
        # vChannelID = 624410188295962664

        # dndfriends
        sChannelID = 651992439263068171 
        vChannelID = 382031984471310336

        sChannel = self.bot.get_channel(sChannelID)
        vChannel = self.bot.get_channel(vChannelID)

        if msg.channel.id == sChannelID and not msg.author.bot:
            author = msg.author 
            content = msg.content

            await msg.delete()

            vEmbed = discord.Embed()
            vEmbed.set_author(name=author, icon_url=author.avatar_url)
            vEmbed.description = content

            vMessage = await vChannel.send(embed=vEmbed)

            await vMessage.add_reaction('✅')
            await vMessage.add_reaction('❌')

        if msg.channel.id == vChannelID:
            sMessage = await sChannel.send(content='Thanks! Your suggestion has been submitted and will be reviewed by the Admin team.')
            await asyncio.sleep(30) 
            await sMessage.delete()


    # @commands.command()
    # async def roleremove(self,ctx):
    #     guild = ctx.guild

    #     print ('start')
    #     i = 0
    #     for m in guild.members:
    #         print (str(i)+ " of " + str(len(guild.members)))
    #         roles = m.roles

    #         if 'True Friend' in[r.name for r in roles]:
    #             addRoles = ['Tier 1', 'Tier 2', 'Tier 3', 'Tier 4', 'D&D Friend']
    #             removeRoles = ["Elite Friend", 'Journeyfriend', 'Junior Friend', 'New Friend']
    #             for a in addRoles:
    #                 add = get(guild.roles, name = a)
    #                 await m.add_roles(add)

    #             for x in removeRoles:
    #                 remove = get(guild.roles, name = x)
    #                 if remove:
    #                     await m.remove_roles(remove)

    #         elif 'Elite Friend' in [r.name for r in roles]:
    #             addRoles = ['Tier 1', 'Tier 2', 'Tier 3', 'D&D Friend']
    #             removeRoles = ['Journeyfriend', 'Junior Friend', 'New Friend']
    #             for a in addRoles:
    #                 add = get(guild.roles, name = a)
    #                 await m.add_roles(add)

    #             for x in removeRoles:
    #                 remove = get(guild.roles, name = x)
    #                 if remove:
    #                     await m.remove_roles(remove)
    #         elif 'Journeyfriend' in [r.name for r in roles]:
    #             addRoles = ['Tier 1', 'Tier 2', 'D&D Friend']
    #             removeRoles = ['Junior Friend', 'New Friend']
    #             for a in addRoles:
    #                 add = get(guild.roles, name = a)
    #                 await m.add_roles(add)

    #             for x in removeRoles:
    #                 remove = get(guild.roles, name = x)
    #                 if remove:
    #                     await m.remove_roles(remove)
    #         if 'D&D Friend' in [r.name for r in roles] and len(roles) == 2:
    #             addRoles = ['Tier 0']
    #             for a in addRoles:
    #                 add = get(guild.roles, name = a)
    #                 await m.add_roles(add)
    #         i+=1

    #     print("done")
        
def setup(bot):
    bot.add_cog(Misc(bot))
