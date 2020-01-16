import discord
import gspread
import decimal
import os
import time
import traceback
# import json
import requests
from discord.ext import commands
import asyncio
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient

from secret import *

def timeConversion (time):
		hours = time//3600
		time = time - 3600*hours
		minutes = time//60
		return ('%d Hours %d Minutes' %(hours,minutes))
		
def getTiers (tiers):
    getTierArray = []
    for i in range(len(tiers)):
        if tiers[i] != "":
            getTierArray.append(i)
    getTierArray.append(len(sheet.row_values(3)) + 1)

    return getTierArray

async def traceBack (ctx,error):
    ctx.command.reset_cooldown(ctx)
    etype = type(error)
    trace = error.__traceback__

    # the verbosity is how large of a traceback to make
    # more specifically, it's the amount of levels up the traceback goes from the exception source
    verbosity = 2

    # 'traceback' is the stdlib module, `import traceback`.
    lines = traceback.format_exception(etype,error, trace, verbosity)

    # format_exception returns a list with line breaks embedded in the lines, so let's just stitch the elements together
    traceback_text = ''.join(lines)

    xyffei = ctx.guild.get_member(220742049631174656)

    await xyffei.send(f"```{traceback_text}```\n")
    await ctx.channel.send(f"Uh oh, looks like this is some unknown error I have ran into. {ctx.guild.get_member(220742049631174656).mention} has been notified.")
    raise error

def calculateTreasure(seconds, role):
    cp = ((seconds + 900) // 1800) / 2
    tp = .5 if cp == .5 else int(decimal.Decimal((cp / 2) * 2).quantize(0, rounding=decimal.ROUND_HALF_UP )) / 2
    gp = cp * 40
    role = role.lower()

    if role == 'journey':
      gp = cp * 120

    if role == "elite":
      tp = cp
      gp = cp * 240

    if role == "true":
      tp = cp
      gp = cp * 600

    # refactor later
    dcp = int(decimal.Decimal((cp / 2) * 2).quantize(0, rounding=decimal.ROUND_HALF_UP )) / 2
    dtp = int(decimal.Decimal((tp / 2) * 2).quantize(0, rounding=decimal.ROUND_HALF_UP )) / 2
    dgp = int(decimal.Decimal((gp / 2) * 2).quantize(0, rounding=decimal.ROUND_HALF_UP )) / 2

    return [cp, tp, gp, dcp, dtp, dgp]

async def callAPI(ctx, apiEmbed="", apiEmbedmsg=None, table=None, query=None):
    channel = ctx.channel
    author = ctx.author

    if query == "" or table is None:
        return None, apiEmbed, apiEmbedmsg

    collection = db[table]
    
    if query is None:
        return list(collection.find()), apiEmbed, apiEmbedmsg

    query = query.replace('(', '\\(')
    query = query.replace(')', '\\)')

    records = list(collection.find({"Name": {"$regex": query.strip(), '$options': 'i' }}))

    print(records)

    if records == list():
        return None, apiEmbed, apiEmbedmsg
    else:
        infoString = ""
        if (len(records) > 1):
            for i in range(0, min(len(records), 9)):
                if table == 'mit':
                    infoString += f"{numberEmojis[i]}: {records[i]['Name']} (Tier {records[i]['Tier']})\n"
                elif table == 'rit':
                    infoString += f"{numberEmojis[i]}: {records[i]['Name']} (Tier {records[i]['Tier']} {records[i]['Minor/Major']})\n"
                else:
                    infoString += f"{numberEmojis[i]}: {records[i]['Name']}\n"
            
            def apiEmbedCheck(r, u):
                sameMessage = False
                if apiEmbedmsg.id == r.message.id:
                    sameMessage = True
                return (r.emoji in numberEmojis[:min(len(records), 9)]) or (str(r.emoji) == '❌') and u == author

            apiEmbed.add_field(name=f"There seems to be multiple results for `{query}`, please choose the correct one.\nIf the result you are looking for is not here, please cancel the command with ❌ and be more specific", value=infoString, inline=False)
            if not apiEmbedmsg:
                apiEmbedmsg = await channel.send(embed=apiEmbed)
            else:
                await apiEmbedmsg.edit(embed=apiEmbed)

            await apiEmbedmsg.add_reaction('❌')

            try:
                tReaction, tUser = await bot.wait_for("reaction_add", check=apiEmbedCheck, timeout=60)
            except asyncio.TimeoutError:
                await apiEmbedmsg.delete()
                await channel.send('Timed out! Try using the command again.')
                ctx.command.reset_cooldown(ctx)
                return None, apiEmbed, apiEmbedmsg
            else:
                if tReaction.emoji == '❌':
                    await apiEmbedmsg.edit(embed=None, content=f"Command canceled. Try using the command again.")
                    await apiEmbedmsg.clear_reactions()
                    ctx.command.reset_cooldown(ctx)
                    return None, apiEmbed, apiEmbedmsg
            apiEmbed.clear_fields()
            await apiEmbedmsg.clear_reactions()
            return records[int(tReaction.emoji[0]) - 1], apiEmbed, apiEmbedmsg

        else:
            return records[0], apiEmbed, apiEmbedmsg

async def checkForChar(ctx, char, charEmbed="", mod=False):
    channel = ctx.channel
    author = ctx.author
    guild = ctx.guild

    playersCollection = db.players
    if mod == True:
        charRecords = list(playersCollection.find({"Name": {"$regex": char, '$options': 'i' }})) 
    else:
        charRecords = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": char, '$options': 'i' }}))

    if charRecords == list():
        if not mod:
            await channel.send(content=f'I was not able to find your character named `{char}`. Please check your spelling and try again')
        ctx.command.reset_cooldown(ctx)
        return None, None

    else:
        if len(charRecords) > 1:
            infoString = ""
            charRecords = list(charRecords)
            for i in range(0, min(len(charRecords), 9)):
                infoString += f"{numberEmojis[i]}: {charRecords[i]['Name']} ({guild.get_member(int(charRecords[i]['User ID']))})\n"
            
            def infoCharEmbedcheck(r, u):
                sameMessage = False
                if charEmbedmsg.id == r.message.id:
                    sameMessage = True
                return (r.emoji in numberEmojis[:min(len(charRecords), 9)]) or (str(r.emoji) == '❌') and u == author

            charEmbed.add_field(name=f"There seems to be multiple results for `{char}`, please choose the correct character.", value=infoString, inline=False)
            charEmbedmsg = await channel.send(embed=charEmbed)
            for num in range(0,min(len(charRecords), 9)): await charEmbedmsg.add_reaction(numberEmojis[num])
            await charEmbedmsg.add_reaction('❌')

            try:
                tReaction, tUser = await bot.wait_for("reaction_add", check=infoCharEmbedcheck, timeout=60)
            except asyncio.TimeoutError:
                await charEmbedmsg.delete()
                await channel.send('Character information timed out! Try using the command again')
                ctx.command.reset_cooldown(ctx)
                return None, None
            else:
                if tReaction.emoji == '❌':
                    await charEmbedmsg.edit(embed=None, content=f"Character information canceled. User `{commandPrefix}char info` command and try again!")
                    await charEmbedmsg.clear_reactions()
                    ctx.command.reset_cooldown(ctx)
                    return None, None
            charEmbed.clear_fields()
            await charEmbedmsg.clear_reactions()
            return charRecords[int(tReaction.emoji[0]) - 1], charEmbedmsg

    return charRecords[0], None

async def checkForGuild(ctx, name):
    channel = ctx.channel
    author = ctx.author
    guild = ctx.guild

    collection = db.guilds
    records = collection.find_one({"Name": {"$regex": name, '$options': 'i' }})

    if not records:
        return False
    else:
        return records
      
def refreshKey (timeStarted):
		if (time.time() - timeStarted > 60 * 59):
				gClient.login()
				print("Sucessfully refreshed OAuth")
				global refreshTime
				refreshTime = time.time()
		return

# use creds to create a client to interact with the Google Drive API
# gSecret = {
#   "type": "service_account",
#   "project_id": "magic-item-table",
#   "private_key_id": os.environ['PKEY_ID'],
#   "private_key": os.environ['PKEY'],
#   "client_email": os.environ['CEMAIL'],
#   "client_id": os.environ['C_ID'],
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": os.environ['C_CERT']
# }

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(gSecret, scope)

gClient = gspread.authorize(creds)
refreshTime = time.time()

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = gClient.open("Magic Item Tables").sheet1
ritSheet = gClient.open("Magic Item Tables").get_worksheet(1)
# charDatabase = gClient.open("Character Database").worksheet("Character Database")
# refListSheet = gClient.open("Character Database").worksheet("Reference Lists")


# sheet = gClient.open("Magic Item Table").sheet1
# ritSheet = gClient.open("Reward Item Table").sheet1

# token = os.environ['TOKEN']
currentTimers = []

gameCategory = ["🎲 game rooms", "🐉 campaigns", "mod friends"]
roleArray = ['Junior', 'Journey', 'Elite', 'True', '']
noodleRoleArray = ['Good Noodle', 'Elite Noodle', 'True Noodle', 'Ramen Noodle', 'Spicy Noodle']
tierArray = getTiers(sheet.row_values(2))
tpArray = sheet.row_values(3)
commandPrefix = '$'
timezoneVar = 'US/Central'

ritTierArray = getTiers(ritSheet.row_values(2))
ritSubArray = ritSheet.row_values(3)

left = '\N{BLACK LEFT-POINTING TRIANGLE}'
right = '\N{BLACK RIGHT-POINTING TRIANGLE}'
back = '\N{LEFTWARDS ARROW WITH HOOK}'

numberEmojisMobile = ['1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣']
numberEmojis = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣']

alphaEmojis = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰',
'🇱','🇲','🇳','🇴','🇵','🇶','🇷','🇸','🇹','🇺','🇻','🇼','🇽','🇾','🇿']

statuses = [f'D&D Friends | {commandPrefix}help', "We're all friends here!", f"See a bug? tell @Xyffei!"]
discordClient = discord.Client()
bot = commands.Bot(command_prefix=commandPrefix, case_insensitive=True)

connection = MongoClient(mongoConnection, ssl=True) 
db = connection.dnd


# API_URL = ('https://api.airtable.com/v0/appF4hiT6A0ISAhUu/'+ 'races')
# # API_URL += '?offset=' + 'itr4Z54rnNABYW8jj/recr2ss2DkyF4Q84X' 
# r = requests.get(API_URL, headers=headers)
# r = r.json()['records']
# playersCollection = db.races
# addList = []
# for i in r:
#     print(i['fields'])
#     addList.append(i['fields'])

# playersCollection.insert_many(addList)


# collection = db['races']

# records = list(collection.find({"Modifiers": {"$regex": '', '$options': 'i' }}))


# i = 0
# for r in sorted(records, key = lambda i: i['Name']) :
#     print(r['Name'])
#     i+=1

# print (i)

# # delete
# collection.remove(({"Modifiers": {"$regex": '', '$options': 'i' }}))