import discord
import asyncio
import requests
import re
from discord.utils import get        
from discord.ext import commands
import sys
import traceback
from bfunc import db, callAPI, traceBack


def admin_or_owner():
    async def predicate(ctx):
        
        role = get(ctx.message.guild.roles, name = "A d m i n")
        output = (role in ctx.message.author.roles) or ctx.message.author.id in [220742049631174656, 203948352973438995]
        return  output
    return commands.check(predicate)

class Admin(commands.Cog, name="Admin"):
    def __init__ (self, bot):
        self.bot = bot
    
    @commands.group()
    async def react(self, ctx):	
        pass
    
    
    @react.command()
    @admin_or_owner()
    async def printGuilds(self, ctx):
        out = "All guild channels:\n"
        ch = ctx.guild.get_channel(452704598440804375)
        for channel in ch.text_channels:
            out+="  "+channel.mention+"\n"
        await ctx.channel.send(content=out)
    
    #this function allows you to specify a channel and message and have the bot react with a given emote
    #Not tested with emotes the bot might not have access to
    @react.command()
    @admin_or_owner()
    async def add(self, ctx, channel: int, msg: int, emote: str):
        ch = ctx.guild.get_channel(channel)
        message = await ch.fetch_message(msg)
        await message.add_reaction(emote)
        await ctx.message.delete()
    
    #Allows the sending of messages
    @commands.command()
    @admin_or_owner()
    async def send(self, ctx, channel: int, *, msg: str):
        ch = ctx.guild.get_channel(channel)
        await ch.send(content=msg)
    
    #this function allows you to specify a channel and message and have the bot remove its reaction with a given emote
    #Not tested with emotes the bot might not have access to
    @react.command()
    @admin_or_owner()
    async def remove(self, ctx, channel: int, msg: int, emote: str):
        ch = ctx.guild.get_channel(channel)
        message = await ch.fetch_message(msg)
        await message.remove_reaction(emote, self.bot.user)
        await ctx.message.delete()


    @commands.command()
    @admin_or_owner()
    async def goldupdate(self, ctx, tier: int, tp: int, gp: int):
        try:
            db.mit.update_many(
               {"Tier": tier, "TP": tp},
               {"$set" : {"GP" : gp}},
            )
            await ctx.channel.send(content=f"Successfully updated the GP cost of all T{tier} items costing {tp} TP to {gp} GP.")
    
        except Exception as e:
            traceback.print_exc()
        
    @commands.command()
    @admin_or_owner()
    async def killbot(self, ctx):
        await self.bot.logout()
    
    @commands.command()
    @admin_or_owner()
    async def reload(self, ctx, cog: str):
        
        try:
            self.bot.reload_extension('cogs.'+cog)
            print(f"{cog} has been reloaded.")
        except commands.ExtensionNotLoaded as e:
            try:
                self.bot.load_extension("cogs." + cog)
                print(f"{cog} has been added.")
            except (discord.ClientException, ModuleNotFoundError):
                print(f'Failed to load extension {cog}.')
                traceback.print_exc()
        except Exception as e:
            print(f'Failed to load extension {cog}.')
            traceback.print_exc()


def setup(bot):
    bot.add_cog(Admin(bot))
