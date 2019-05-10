import discord
import gspread
import decimal
import os
from oauth2client.service_account import ServiceAccountCredentials
from string import ascii_lowercase
import json
# from secret import *



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

client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("Magic Item Table (Bot)").sheet1
ritSheet = client.open("Reward Item Table (Bot)").sheet1
# token = os.environ['TOKEN']
client = discord.Client()

gameCategory = "Game Rooms"
roleArray = ['Junior', 'Journey', 'Elite', 'True']
tierArray = getTiers(sheet.row_values(2))
tpArray = sheet.row_values(3)
alphabetList = list(ascii_lowercase)
commandPrefix = '.'
timezoneVar = 'US/Central'

ritTierArray = getTiers(ritSheet.row_values(2))
ritSubArray = ritSheet.row_values(3)

one = '1⃣'
two = '2⃣'
three = '3⃣'
four = '4⃣'

left = '\N{BLACK LEFT-POINTING TRIANGLE}'
right = '\N{BLACK RIGHT-POINTING TRIANGLE}'
back = '\N{LEFTWARDS ARROW WITH HOOK}'

numberEmojis = ['1⃣','2⃣','3⃣','4⃣','5⃣','6⃣','7⃣','8⃣','9⃣','🔟',]

alphaEmojis = ['🇦','🇧','🇨','🇩','🇪','🇫','🇬','🇭','🇮','🇯','🇰',
'🇱','🇲','🇳','🇴','🇵','🇶','🇷','🇸','🇹','🇺','🇻','🇼','🇽','🇾','🇿']