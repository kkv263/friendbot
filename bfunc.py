import discord
import gspread
import decimal
import os
import time
import json
import requests
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

def callAPI(table, query):
    if query == "":
        return False

    API_URL = ('https://api.airtable.com/v0/appF4hiT6A0ISAhUu/'+ table +'?&filterByFormula=(FIND(LOWER(SUBSTITUTE("' + query.replace(" ", "%20") + '"," ","")),LOWER(SUBSTITUTE({Name}," ",""))))').replace("+", "%2B") 
    r = requests.get(API_URL, headers=headers)
    r = r.json()

    if r['records'] == list():
        return False
    else:
        if (len(r['records']) > 1):
            if table == 'Races' or table == "Background":
                for x in r['records']:
                    print(x['fields']['Name'])
                    print(query)
                    if len(x['fields']['Name'].replace(" ", "")) == len(query.replace(" ", "")):
                        return x['fields']

            if table == 'RIT':
                minimum = {'fields': {'Tier': 0}}
                for x in r['records']:
                    if int(x['fields']['Tier']) > int(minimum['fields']['Tier']):
                        min = x
                
                return min['fields']

        else:
            return r['records'][0]['fields']

def callShopAPI(table, query):
    if query == "":
        return False

    API_URL = ('https://api.airtable.com/v0/apprmgL8TfOUoJfl4/'+ table +'?&filterByFormula=(FIND(LOWER(SUBSTITUTE("' + query.replace(" ", "%20") + '"," ","")),LOWER(SUBSTITUTE({Name}," ",""))))').replace("+", "%2B") 
    r = requests.get(API_URL, headers=headers)
    r = r.json()

    if r['records'] == list():
        return False
    else:
        if (len(r['records']) > 1):
            if table == 'Races' or table == "Background":
                for x in r['records']:
                    print(x['fields']['Name'])
                    print(query)
                    if len(x['fields']['Name'].replace(" ", "")) == len(query.replace(" ", "")):
                        return x['fields']

            if table == 'RIT':
                minimum = {'fields': {'Tier': 0}}
                for x in r['records']:
                    if int(x['fields']['Tier']) > int(minimum['fields']['Tier']):
                        min = x
                
                return min['fields']

        else:
            return r['records'][0]['fields']

async def checkForChar(ctx, char, charEmbed=""):
    channel = ctx.channel
    author = ctx.author
    guild = ctx.guild

    playersCollection = db.players
    charRecords = list(playersCollection.find({"User ID": str(author.id), "Name": {"$regex": char, '$options': 'i' }}))

    if charRecords == list():
        await channel.send(content=f'I was not able to find your character named {char}. Please check your spelling and try again')
        self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
        return None, None

    else:
        if len(charRecords) > 1:
            infoString = ""
            charRecords = list(charRecords)
            print(charRecords)
            for i in range(0, min(len(charRecords), 9)):
                infoString += f"{numberEmojis[i]}: {charRecords[i]['Name']}\n"
            
            try:
                def infoCharEmbedcheck(r, u):
                    sameMessage = False
                    if charEmbedmsg.id == r.message.id:
                        sameMessage = True
                    return (r.emoji in numberEmojis[:min(len(charRecords), 9)]) or (str(r.emoji) == '❌') and u == author

                charEmbed.add_field(name=f"There seems to be multiple results for `{char}`, please choose the correct character.", value=infoString, inline=False)
                charEmbedmsg = await channel.send(embed=charEmbed)
                for num in range(0,min(len(charRecords), 6)): await charEmbedmsg.add_reaction(numberEmojis[num])
                await charEmbedmsg.add_reaction('❌')
                tReaction, tUser = await self.bot.wait_for("reaction_add", check=infoCharEmbedcheck, timeout=60)
            except asyncio.TimeoutError:
                await charEmbedmsg.delete()
                await channel.send('Character information timed out! Try using the command again')
                self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
                return None, None
            else:
                if tReaction.emoji == '❌':
                    await charEmbedmsg.edit(embed=None, content=f"Character information canceled. User `{commandPrefix}char info` command and try again!")
                    await charEmbedmsg.clear_reactions()
                    self.char.get_command(ctx.invoked_with).reset_cooldown(ctx)
                    return None, None
            charEmbed.clear_fields()
            await charEmbedmsg.clear_reactions()
            return charRecords[int(tReaction.emoji[0]) - 1], charEmbedmsg

    return charRecords[0], None

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
discordClient = discord.Client()

gameCategory = ["🎲 game rooms", "🐉 campaigns", "mod friends"]
roleArray = ['Junior', 'Journey', 'Elite', 'True', '']
noodleRoleArray = ['Good Noodle', 'Elite Noodle', 'True Noodle', 'Mega Noodle']
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

connection = MongoClient(mongoConnection) 
db = connection.dnd