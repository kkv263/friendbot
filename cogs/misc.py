import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands

class Misc(commands.Cog):
    def __init__ (self, bot):
        self.bot = bot
        self.current_message= None
        #0: No message search so far, 1: Message searched, but no new message made so far, 2: New message made
        self.past_message_check= 0
        self.quest_board_channel_id = 382027190633627649 #382027190633627649 725577624180621313
        self.category_channel_id = 382027737189056544 #382027737189056544  728456686024523810

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
    
        #searches for the last message sent by the bot in case a restart was made
    #Allows it to use it to remove the last post
    async def find_message(self):
        #block any check but the first one
        if(not self.past_message_check):
            self.past_message_check= 1
            self.current_message = await self.bot.get_channel(self.quest_board_channel_id).history().get(author__id = self.bot.user.id)
    
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
            
    @commands.group()
    @admin_or_owner()
    async def version(self, ctx):
        print(discord.__version__)
    
    #A function that grabs all messages in the quest board and compiles a list of availablities
    async def generateMessageText(self):
        tChannel = self.quest_board_channel_id
        channel= self.bot.get_channel(tChannel)
        #get all game channel ids
        game_channel_category =self.bot.get_channel(self.category_channel_id)
        game_channel_ids = set(map(lambda c: c.id, game_channel_category.text_channels))
        build_message = "The current status of the game channels is:\n"
        #create a dictonary to store the room/user pairs
        tierMap = {"Tier 0" : "T0", "Tier 1" : "T1", "Tier 2" : "T2", "Tier 3" : "T3", "Tier 4" : "T4"}
        channel_dm_dic = {}
        for c in game_channel_category.text_channels:
            channel_dm_dic[c.mention]= ["✅ "+c.mention+": Clear", set([])]
        #get all posts in the channel
        all_posts = await channel.history(oldest_first=True).flatten()
        for elem in all_posts:
            #ignore self and Ghost example post
            if(elem.author.id==self.bot.user.id or elem.id == 540049894598246420):
                continue
            #loop in order to avoid guild channels blocking the check
            for mention in elem.channel_mentions:
                if mention.id in game_channel_ids:
                    username = elem.author.name
                    if(elem.author.nick):
                        username = elem.author.nick
                    channel_dm_dic[mention.mention][0] = "❌ "+mention.mention+": "+username
                    for tierMention in elem.role_mentions:
                        print(tierMention)
                        if tierMention.name in tierMap:
                            channel_dm_dic[mention.mention][1].add(tierMap[tierMention.name])
        #build the message using the pairs built above
        print(channel.guild.me)
        for c in game_channel_category.text_channels:
            print(c, c.permissions_for(channel.guild.me).view_channel)
            if(c.permissions_for(channel.guild.me).view_channel):
                tierAddendum = ""
                if(len(channel_dm_dic[c.mention][1])> 0):
                    tierAddendum = " - "+"/".join(sorted(channel_dm_dic[c.mention][1]))
                build_message+=channel_dm_dic[c.mention][0]+tierAddendum+"\n"
        return build_message
    
        
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        tChannel = self.quest_board_channel_id
        """ 
        #if in the correct channel and the message deleted was not the last QBAP
        if(payload.channel_id==tChannel and (not self.current_message or payload.message_id != self.current_message.id)):
            await self.find_message()
            #Since we dont know whose post was deleted we need to cover all the posts to find availablities
            #Also protects against people misposting
            new_text = await (self.generateMessageText)()
            #if we created the last message during current runtime we can just edit
            if(self.current_message and self.past_message_check != 1):
                await self.current_message.edit(content=new_text)
            else:
                #otherwise delete latest message if possible and resend to get back to the bottom
                if(self.current_message):
                    await self.current_message.delete()
                self.past_message_check = 2
                self.current_message = await self.bot.get_channel(self.quest_board_channel_id).send(content=new_text)
           """  
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
    
        tChannel = self.quest_board_channel_id
        """
        if(int(payload.data["channel_id"])==tChannel and (not self.current_message or payload.message_id != self.current_message.id)):
            await self.find_message()
            new_text = await (self.generateMessageText)()
            if(self.current_message and self.past_message_check != 1):
                #in case a message is posted without a game channel which is then edited in we need to this extra check
                msgAfter = False
                async for message in self.bot.get_channel(self.quest_board_channel_id).history(after=self.current_message, limit=1):
                    msgAfter = True
                if( not msgAfter):
                    await self.current_message.edit(content=new_text)
                else:
                    await self.current_message.delete()
                    self.current_message = await self.current_message.send(content=new_text)
            else:
                self.past_message_check = 2
                if(self.current_message):                
                    msgAfter = False
                    async for message in self.bot.get_channel(self.quest_board_channel_id).history(after=self.current_message, limit=1):
                        msgAfter = True
                    if(not msgAfter):
                        await self.current_message.edit(content=new_text)
                        return
                    else:
                        await self.current_message.delete()
                self.current_message = await self.bot.get_channel(self.quest_board_channel_id).send(content=new_text)
               """ 
    @commands.Cog.listener()
    async def on_message(self,msg):
        tChannel = self.quest_board_channel_id
        if(msg.type.value == 7):
            await msg.add_reaction('👋')
        #check if any tier boost was done and react
        elif(7 < msg.type.value and msg.type.value < 12):
            await msg.add_reaction('<:boost:585637770970660876>')
        elif any(word in msg.content.lower() for word in ['thank', 'thanks', 'thank you', 'thx', 'gracias', 'danke']) and 'bot friend' in msg.content.lower():
            await msg.add_reaction('❤️')
            await msg.channel.send("You're welcome friend!")
        elif msg.channel.id == tChannel and msg.author.id != self.bot.user.id:
            """
            await self.find_message()
            server = msg.guild
            channel = msg.channel
            game_channel_category = server.get_channel(self.category_channel_id)
            cMentionArray = msg.channel_mentions
            game_channel_ids = list(map(lambda c: c.id, game_channel_category.text_channels))
            for mention in cMentionArray:
                if mention.id in game_channel_ids:
                    new_text = await (self.generateMessageText)()
                    if(self.past_message_check == 2):
                        await self.current_message.delete()
                        self.current_message = await msg.channel.send(content=new_text)
                        return
                    #if there is an old message our record could be out of date so we need to regather info and go to the bottom
                    elif(self.past_message_check == 1 and self.current_message):
                        await self.current_message.delete()
                    self.past_message_check = 2
                    self.current_message = await msg.channel.send(content=new_text)
                    return
            return
            """
            
        
def setup(bot):
    bot.add_cog(Misc(bot))
