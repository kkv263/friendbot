import discord
import re
from discord.ext import commands
from bfunc import roleArray, calculateTreasure, timeConversion 

class Reward(commands.Cog):
		def __init__ (self, bot):
				self.bot = bot

		@commands.cooldown(1, 5, type=commands.BucketType.member)
		@commands.command()
		async def reward(self,ctx, timeString, tier):
				def convert_to_seconds(s):
						return int(s[:-1]) * seconds_per_unit[s[-1]]

				seconds_per_unit = { "m": 60, "h": 3600 }
				lowerTimeString = timeString.lower()
				tierName = tier.lower().capitalize()
				channel = ctx.channel

				if tierName not in roleArray:
						await channel.send(content='You did not type a valid tier. The valid tiers are: ' + ', '.join(roleArray))
						return


				l = list((re.findall('.*?[hm]', lowerTimeString)))
				totalTime = 0
				for timeItem in l:
						totalTime += convert_to_seconds(timeItem)

				if totalTime == 0:
						await channel.send(content='You may have formatted the time incorrectly or calculated for 0. Try again with the correct format.')
						return

				treasureArray = calculateTreasure(totalTime, tier)
				durationString = timeConversion(totalTime)
				treasureString = f"{treasureArray[0]} CP, {treasureArray[1]} TP, and {treasureArray[2]} GP"
				dmTreasureString = f"{treasureArray[3]} CP, {treasureArray[4]} TP, and {treasureArray[5]} GP"
				await channel.send(content= f"A {durationString} game would give a {tierName} Friend\n\n**Player:** {treasureString} \n**DM:** {dmTreasureString}")

def setup(bot):
    bot.add_cog(Reward(bot))
