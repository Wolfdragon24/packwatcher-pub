#import
import discord
import requests
import os
import asyncio
import json
import re
import datetime
import time
import traceback
import string
import ast
import copy
import base64

from discord.ext import commands, tasks
from pymongo import MongoClient
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from discord.ext.tasks import loop
from concurrent.futures import ThreadPoolExecutor
from pytz import timezone
from github import Github
from urllib3 import Retry

#db setup
cluster = MongoClient("")
db = cluster["discordbot"]
settings = db["settings"]

savesets = list(settings.find())

def getindex(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

#paste.ee setup
dkey = ""
ukey = ""
key = ""
headers = {'X-Auth-Token': ukey}

#github repo setup
githubpat = ""
g = Github(githubpat, retry = Retry(total = 10, status_forcelist = (500, 502, 504), backoff_factor = 0.3))
repo = g.get_user().get_repo("packwatcher-data")

wynnheader = {"apikey":""}

aus = timezone("Australia/Sydney")

srvtrack = {}

settings.update_one({"scope":"global"},{"$set": {"scope":"global"}}, True)

try:
    territories = savesets[0]["territories"]
except:
    territories = {'Lux Nova': {'Aldorei & Surrounds': ["Aldorei's River", 'Aldorei Lowlands', 'Aldorei Valley Upper', 'Aldorei Valley Mid', 'Aldorei Valley Lower', "Aldorei's Waterfall", 'Aldorei Valley South Entrance', 'Aldorei Valley West Entrance', "Aldorei's North Exit", 'Mantis Nest', 'Light Forest South Exit'], 'Cinfras & Surrounds': ['Cinfras County Mid-Upper', 'Cinfras County Mid-Lower', 'Cinfras County Lower', "Cinfras's Small Farm"], 'Canyon Strip': ['Path To The Arch', 'Ghostly Path', 'Burning Farm', 'Burning Airship', 'Cinfras Thanos Transition', 'Bandit Cave Upper']}}    #{"Lux Nova":{"Cinfras Surrounds":["Mesquis Tower","Path to Cinfras","Cinfras Entrance","Cinfras's Small Farm","Cinfras County Lower","Cinfras County Mid-Lower","Cinfras County Mid-Upper","Cinfras County Upper"],"Light Forest & Surrounds":["Light Forest East Upper","Light Forest East Mid","Light Forest Canyon","Light Forest North Exit","Light Forest East Lower","Mantis Nest","Light Forest South Exit","Hobbit River"],"Aldorei & Surrounds":["Aldorei Valley West Entrance","Aldorei Valley Lower","Aldorei Valley Mid","Aldorei Valley Upper","Aldorei's Waterfall","Aldorei's River","Aldorei Lowlands","Aldorei Valley South Entrance","Aldorei's North Exit"],"Gylia Lake":["Gylia Lake South East","Gylia Lake South West","Gylia Lake North East","Gylia Lake North West"],"Camp & Surrounds":["Jitak’s Farm","Gert Camp"]}}
    #{"Lux Nova":{"Ragni":["Ragni","Ragni North Entrance","Ragni North Suburbs","Ragni East Suburbs","Ragni Main Entrance"],"Ragni Surrounds":["Katoa Ranch","Ragni Plains", "Maltic Plains", "Plains"],"Nivla":["Nivla Forest Entrance","Nivla Forest","North Nivla Forest","Nivla Forest Exit","South Nivla Forest","Nivla Forest Edge"],"Elkurn Surrounds":["Road to Elkurn","Elkurn Fields","Elkurn","Animal Bridge"],"Ravines & Surrounds":["Pigmen Ravines Entrance","Pigmen Ravines","South Pigmen Ravines","Abandoned Farm","Road to Time Valley","Time Valley","Little Wood","Jungle Lake"],"Maltic Surrounds":["Maltic","Maltic Coast","Farmers Valley","Coastal Trail"]}}
    settings.update_one({"scope":"global"},{"$set": {"territories":territories}})

try:
    allies = savesets[0]["allies"]
except:
    allies = []

try:
    hqter = savesets[0]["critter"]["hq"]
    othercrit = savesets[0]["critter"]["othercrit"]
except:
    hqter = ""
    othercrit = []

try:
    trackerchannels = ast.literal_eval(savesets[0]["trackerchannels"])
except:
    trackerchannels = {790039177928114226:True,804093579609636874:False}
    settings.update_one({"scope":"global"},{"$set": {"trackerchannels":str(trackerchannels)}})

try:
    hourpingtracker = savesets[0]["hourpingtracker"]
except:
    hourpingtracker = 15
    settings.update_one({"scope":"global"},{"$set": {"hourpingtracker":hourpingtracker}})

try:
    resrvtracker = savesets[0]["resrvtracker"]
except:
    resrvtracker = 0
    settings.update_one({"scope":"global"},{"$set": {"resrvtracker":resrvtracker}})

try:
    fallbackmode = savesets[0]["fallbackmode"]
except:
    fallbackmode = {"territory":False,"sessions":False}
    settings.update_one({"scope":"global"},{"$set": {"fallbackmode":fallbackmode}})

infodown = {"sessionsmain":False,"sessionsbackup":False,"guilds":False,"monthlyxp":False}
terupdateerr = False
sessionsmainupdateerr = False
sessionsbackupupdateerr = False
guildsupdateerr = False
monthlyxpupdateerr = False
xpmonthdone = False
lastoutput = None

def ffacheck(ter):
    for terarea in territories["Lux Nova"]:
        if ter['territory'] in territories["Lux Nova"][terarea]:
            return False
    return True

def GetKey(title):
    pastelst = requests.get("https://api.paste.ee/v1/pastes", headers=headers).json()
    for paste in pastelst["data"]:
        if paste["description"] == title:
            return paste["id"]

    payload = {"description":title, "expiration":"31536000", "sections":[{"contents":str({})}]}
    send = requests.post("https://api.paste.ee/v1/pastes",json=payload,headers=headers).json()
    return send["id"]

def GetKey(title):
    pastelst = requests.get("https://api.paste.ee/v1/pastes", headers=headers).json()
    for paste in pastelst["data"]:
        if paste["description"] == title:
            return paste["id"]

    payload = {"description":title, "expiration":"31536000", "sections":[{"contents":"{}"}]}
    send = requests.post("https://api.paste.ee/v1/pastes",json=payload,headers=headers).json()
    return send["id"]

def PasteFetch(title):
    key = GetKey(title)

    pastedata = requests.get(f"https://api.paste.ee/v1/pastes/{key}", headers=headers).text
    loaded = json.loads(pastedata.replace("\"None\"","None").replace("\'","\""))
    data = loaded["paste"]["sections"][0]["contents"]
    try:
        data = json.loads(data)
    except:
        data = ast.literal_eval(data)
    return data

try:
    guildlst = PasteFetch("Guild List")
except:
    infodown["guilds"] = True

tempsessions = {}
onlineplyrs = []
backuptempsessions = {}
backuponlineplyrs = []

def GuildListUpdate():

    key = GetKey("Guild List")

    guildfl = requests.get("https://api.wynncraft.com/public_api.php?action=guildList", params=wynnheader).json()

    checklist = []

    for guildname in guildfl['guilds']:
        if guildname not in guildlst.values() and not any(guildname in guildnames for guildnames in guildlst.values()):
            checklist.append(guildname)

    for guildname in checklist:
        ngldinfo = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildname}", params=wynnheader).json()
        try:
            pref = (ngldinfo["prefix"]).lower()
        except:
            pass
        if pref in guildlst:
            guildlst[pref] += f'|{guildname}'
        else:
            guildlst[pref] = guildname
        time.sleep(0.6)

    pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{key}", headers=headers).json()

    payload = {"description":"Guild List", "expiration":"31536000", "sections":[{"contents":str(guildlst).replace("\'","\"")}]}
    pastecr = requests.post("https://api.paste.ee/v1/pastes", json=payload, headers=headers)
    guildsupdateerr = False
    infodown["guilds"] = False

def GuildXPContrUpdate():
    gkey = GetKey("Gained Guild XP Contributions")
    gained = PasteFetch("Gained Guild XP Contributions")#gained:{"data":[]}
    skey = GetKey("Stored Guild XP Contributions")
    old = PasteFetch("Stored Guild XP Contributions") #old:{"data":[],"timestamp":""}

    currenttime = datetime.now(aus)
    conglodata = currenttime.strftime("%d/%m/%y")

    try:
        if old["timestamp"] == conglodata:
            return
    except:
        pass

    newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Lux Nova", params=wynnheader).json()
    members = newdata["members"]

    try:
        oldmem = old["data"]
    except:
        old["data"] = []
    try:
        gndmem = gained["data"]
    except:
        gained["data"] = []

    #update the stored values
    toupdatelst = []
    for member in members:
        if any(member["name"] == loggedmember["name"] for loggedmember in old["data"]):
            workingdata = next(loggedmember for loggedmember in old["data"] if loggedmember["name"] == member["name"])
        else:
            workingdata = {"name":member["name"],"uuid":member["uuid"],"contr":0}
            old["data"].append(workingdata)

        if workingdata["contr"] < member["contributed"]:
            change = member["contributed"] - workingdata["contr"]
            workingdata["contr"] = member["contributed"]

            toupdatelst.append({"name":workingdata["name"],"uuid":workingdata["uuid"],"change":change})
        elif workingdata["contr"] > member["contributed"]:
            change = member["contributed"]
            workingdata["contr"] += member["contributed"]

            toupdatelst.append({"name":workingdata["name"],"uuid":workingdata["uuid"],"change":change})

    gained["data"].append({"date":conglodata,"data":toupdatelst})
    old["timestamp"] = conglodata

    pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{gkey}", headers=headers).json()
    pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{skey}", headers=headers).json()

    gainedpayload = {"description":"Gained Guild XP Contributions", "expiration":"31536000", "sections":[{"contents":str(gained).replace("\'","\"")}]}
    gainedpaste = requests.post("https://api.paste.ee/v1/pastes", json=gainedpayload, headers=headers)
    storedpayload = {"description":"Stored Guild XP Contributions", "expiration":"31536000", "sections":[{"contents":str(old).replace("\'","\"")}]}
    storedpastecr = requests.post("https://api.paste.ee/v1/pastes", json=storedpayload, headers=headers)

@loop(hours=12)
async def loadgldupdt():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), GuildListUpdate)
    except:
        infodown["guilds"] = True

@loop(hours=1)
async def loadguildxpupdt():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), GuildXPContrUpdate)
    except:
        infodown["monthlyxp"] = True

storedchanging = {}
storedplaytime = {}
storedmembers = {}
changingcounter = 0
rankselection = {"OWNER":1,"CHIEF":2,"STRATEGIST":3,"CAPTAIN":4,"RECRUITER":5,"RECRUIT":6,"NOT IN GUILD":7}
revrankselection = {1:"OWNER",2:"CHIEF",3:"STRATEGIST",4:"CAPTAIN",5:"RECRUITER",6:"RECRUIT",7:"NOT IN GUILD"}
nialeftmem = []
niajoinmem = []
niaalertchannels = [861058162354159616,766402801479188490] #861058162354159616,766402801479188490
lxaleftmem = []
lxajoinmem = []
lxaalertchannels = [863897825119830036]
stuckplayers = []
playtimeerrors = []

guildstocheck = ["Nerfuria","Lux Nova","First Fleet"]

playfile = None
memfile = None

def get_month_day_range(date):
    first_day = date.replace(day = 1)
    last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day

def getdata(filename):
    try:
        data = repo.get_contents(filename).decoded_content.decode().replace("'","\"")
        return (repo.get_contents(filename), json.loads(data))
    except:
        ref = repo.get_git_ref("heads/main")
        tree = repo.get_git_tree(ref.object.sha, recursive='/' in filename).tree
        sha = [x.sha for x in tree if x.path == filename]
        if not sha:
            file = repo.create_file(filename, "Automated Data Generation","{}")["content"]
            return(file,{})
        else:
            data = base64.b64decode(repo.get_git_blob(sha[0]).content).decode().replace("'","\"")
            return (repo.get_git_blob(sha[0]), json.loads(data))

def PlaytimeUpdate():

    global storedplaytime
    global storedchanging
    global storedmembers
    global changingcounter
    global playfile
    global memfile
    global nialeftmem
    global niajoinmem
    global lxaleftmem
    global lxajoinmem
    global stuckplayers
    global playtimeerrors

    #gets data
    if not storedplaytime:
        try:
            playfile, storedplaytime = getdata("playtime.txt")
        except:
            storedplaytime = {} #storedplaytime = {"texttime":[{"uuid":uuid}]}
    if not storedchanging:
        try:
            storedchanging = PasteFetch("Playtime Change Data")
        except:
            storedchanging = {}
    if not storedmembers:
        try:
            memfile, storedmembers = getdata("members.txt")
        except:
            storedmembers = {}

    oldstored = copy.deepcopy(storedplaytime)
    oldmembers = copy.deepcopy(storedmembers)

    totalonline = []

    #gets list of all players online
    onlineplayers = requests.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers", params=wynnheader).json()
    for world in onlineplayers:
        if world != "request":
            totalonline.extend(onlineplayers[world])

    #gets current time
    nowtime = datetime.now(aus)
    texttime = nowtime.strftime("%H-%d/%m/%y")
    textday = nowtime.strftime("%d/%m/%y")
    lasttextday = (nowtime - timedelta(days=1)).strftime("%d/%m/%y")

    guildplayers = {}
    guildplayersid = {}

    for guild in guildstocheck:
        data = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}", params=wynnheader).json()
        prefix = data["prefix"]
        try:
            guildplayers[prefix] = [member["name"] for member in data["members"]]
        except:
            playtimeerrors.append({"type":f"username for guild: '{prefix}'","data":data})
        try:
            guildplayersid[prefix] = [member["uuid"] for member in data["members"]]
        except:
            playtimeerrors.append({"type":f"uuid for guild: '{prefix}'","data":data})

        for player in guildplayersid[prefix]:
            try:
                pdata = requests.get(f"https://playerdb.co/api/player/minecraft/{player}").json()
                uname = pdata["data"]["player"]["username"]
                if uname not in guildplayers[prefix]:
                    guildplayers[prefix].append(uname)
            except:
                playtimeerrors.append({"type":"player fetch for guild members","data":pdata})

    #adds a minute to online players
    for player in totalonline:
        if any(player in guildplayers[prefix] for prefix in guildplayers):
            if player not in storedchanging:
                storedchanging[player] = 0
            else:
                storedchanging[player] += 1

    toclear = []
    try:
        if storedmembers[textday]["Nia"] != guildplayersid["Nia"]:
            leftmem = [uuid for uuid in storedmembers[textday]["Nia"] if uuid not in guildplayersid["Nia"]]
            nialeftmem.extend(leftmem)
            joinmem = [uuid for uuid in guildplayersid["Nia"] if uuid not in storedmembers[textday]["Nia"]]
            niajoinmem.extend(joinmem)
    except:
        try:
            if storedmembers[lasttextday]["Nia"] != guildplayersid["Nia"]:
                leftmem = [uuid for uuid in storedmembers[lasttextday]["Nia"] if uuid not in guildplayersid["Nia"]]
                nialeftmem.extend(leftmem)
                joinmem = [uuid for uuid in guildplayersid["Nia"] if uuid not in storedmembers[lasttextday]["Nia"]]
                niajoinmem.extend(joinmem)
        except:
            pass

    try:
        if storedmembers[textday]["LXA"] != guildplayersid["LXA"]:
            leftmem = [uuid for uuid in storedmembers[textday]["LXA"] if uuid not in guildplayersid["LXA"]]
            lxaleftmem.extend(leftmem)
            joinmem = [uuid for uuid in guildplayersid["LXA"] if uuid not in storedmembers[textday]["LXA"]]
            lxajoinmem.extend(joinmem)
    except:
        try:
            if storedmembers[lasttextday]["LXA"] != guildplayersid["LXA"]:
                leftmem = [uuid for uuid in storedmembers[lasttextday]["LXA"] if uuid not in guildplayersid["LXA"]]
                lxaleftmem.extend(leftmem)
                joinmem = [uuid for uuid in guildplayersid["LXA"] if uuid not in storedmembers[lasttextday]["LXA"]]
                lxajoinmem.extend(joinmem)
        except:
            pass

    storedmembers[textday] = guildplayersid

    #adds players to stored data if previously online
    for player in storedchanging:
        if player not in totalonline:

            if texttime not in storedplaytime:
                storedplaytime[texttime] = []

            try:
                data = requests.get(f"https://playerdb.co/api/player/minecraft/{player}").json()
            except:
                playtimeerrors.append({"type":"player fetch for previously online","data":data})
            try:
                uuid = data["data"]["player"]["id"]
            except:
                stuckplayers.append(player)

            prefix = next((prefix for prefix in guildplayers if player in guildplayers[prefix]),None)
            if prefix:
                inputteddata = {"uuid":uuid,"duration":storedchanging[player],"guild":prefix}
                (storedplaytime[texttime]).append(inputteddata)

                toclear.append(player)

    for player in (stuckplayers + toclear):
        try:
            del storedchanging[player]
        except:
            playtimeerrors.append({"type":f"failed clear '{player}' from storedchanging","data":storedchanging})

    if changingcounter >= 5:

        changingcounter = 0

        try:
            #update pastes
            ckey = GetKey("Playtime Change Data")
            pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{ckey}", headers=headers)

            changingpayload = {"description":"Playtime Change Data", "expiration":"31536000", "sections":[{"contents":str(storedchanging).replace("\'","\"")}]}
            changingpaste = requests.post("https://api.paste.ee/v1/pastes", json=changingpayload, headers=headers)
        except:
            error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
            playtimeerrors.append({"type":"playtime update file for paste.ee","data":error})

    if not storedplaytime or storedplaytime != oldstored:
        if playfile:
            try:
                playfile = repo.update_file("playtime.txt", "Automated Data Generation", str(storedplaytime), playfile.sha)["content"]
            except:
                error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                playtimeerrors.append({"type":"playtime update file for github","data":error})
        else:
            try:
                playfile = repo.create_file("playtime.txt", "Automated Data Generation",str(storedplaytime))["content"]
            except:
                error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                playtimeerrors.append({"type":"playtime create file for github","data":error})
    if not storedmembers or storedmembers != oldmembers:
        if memfile:
            try:
                memfile = repo.update_file("members.txt", "Automated Data Generation", str(storedmembers), memfile.sha)["content"]
            except:
                error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                playtimeerrors.append({"type":"member update file for github","data":error})
        else:
            try:
                memfile = repo.create_file("members.txt", "Automated Data Generation",str(storedmembers))["content"]
            except:
                error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                playtimeerrors.append({"type":"member create file for github","data":error})

    changingcounter += 1

@loop(minutes=1)
async def loadplaytimeupd():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), PlaytimeUpdate)
    except:
        pass

#COMMAND RATELIMITING
ratelimitedusers = {} #format userid:{"usertype":(exclusive/owner/normal),"requesttype":(playtime),"sendtime":datetimeobj,"endtime:datetimeobj"}

try:
    exclusiveusers = savesets[0]["exclusers"]
except:
    exclusiveusers = []

owner = 276976462140014593

def process_ratelimit(userid,requesttype):
    if requesttype in ["activity","playtime","xp"]:
        currenttime = datetime.now(aus)

        if userid == owner:
            usertype = "owner"
            additive = 0
        elif userid in exclusiveusers:
            usertype = "exclusive"
            additive = 3
        else:
            usertype = "normal"
            additive = 10

        endtime = currenttime + timedelta(seconds=additive)

        ratelimitedusers[userid] = {"usertype":usertype,"requesttype":requesttype,"sendtime":currenttime,"endtime":endtime}

class WynnModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.OwnedTersUpdate.start()

    @loop(minutes=2)
    async def OwnedTersUpdate(self):
        await self.bot.wait_until_ready()
        global terupdateerr
        global resrvtracker
        global hourpingtracker
        global sessionsmainupdateerr
        global sessionsbackupupdateerr
        global guildsupdateerr
        global fallbackmode
        global monthlyxpupdateerr
        global allies
        global lastoutput
        global hqter
        global othercrit
        global nialeftmem
        global niajoinmem
        global niaalertchannels
        global lxaleftmem
        global lxajoinmem
        global lxaalertchannels
        global stuckplayers
        global playtimeerrors

        errorchannel = self.bot.get_channel(837917735089340446)

        try:
            updter = requests.get("https://api.wynncraft.com/public_api.php?action=territoryList", params=wynnheader).json()
            terlist = updter["territories"]

            ownedcount = 0
            lostcount = 0
            ownedffas = 0
            alliesowned = 0

            cong = []

            embed = discord.Embed(title="Lux Nova - Continued Territory Status", color=0xa049b8)

            for territoryarea in territories["Lux Nova"]:
                terstatus = ""
                for indvterritory in territories["Lux Nova"][territoryarea]:
                    if fallbackmode:
                        try:
                            if terstatus == "":
                                if terlist[indvterritory]["guild"] == "Lux Nova":
                                    terstatus = f"{indvterritory}: 🟢"
                                    ownedcount += 1
                                    cong.append(f"{indvterritory}: 🟢")
                                elif terlist[indvterritory]["guild"] in allies:
                                    terstatus = f"{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                    alliesowned += 1
                                    cong.append(f"{indvterritory}: 🔵")
                                else:
                                    terstatus = f"{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                    lostcount += 1
                                    cong.append(f"{indvterritory}: 🔴")
                            else:
                                if terlist[indvterritory]["guild"] == "Lux Nova":
                                    terstatus += f"\n{indvterritory}: 🟢"
                                    ownedcount += 1
                                    cong.append(f"{indvterritory}: 🟢")
                                elif terlist[indvterritory]["guild"] in allies:
                                    terstatus += f"\n{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                    alliesowned += 1
                                    cong.append(f"{indvterritory}: 🔵")
                                else:
                                    terstatus += f"\n{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                    lostcount += 1
                                    cong.append(f"{indvterritory}: 🔴")
                        except:
                            if terstatus == "":
                                terstatus = f"{indvterritory}: Invalid Territory"
                            else:
                                terstatus += f"\n{indvterritory}: Invalid Territory"
                    else:
                        if terstatus == "":
                            if terlist[indvterritory]["guild"] == "Lux Nova":
                                terstatus = f"{indvterritory}: 🟢"
                                ownedcount += 1
                                cong.append(f"{indvterritory}: 🟢")
                            elif terlist[indvterritory]["guild"] in allies:
                                terstatus = f"{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                alliesowned += 1
                                cong.append(f"{indvterritory}: 🔵")
                            else:
                                terstatus = f"{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                lostcount += 1
                                cong.append(f"{indvterritory}: 🔴")
                        else:
                            if terlist[indvterritory]["guild"] == "Lux Nova":
                                terstatus += f"\n{indvterritory}: 🟢"
                                ownedcount += 1
                                cong.append(f"{indvterritory}: 🟢")
                            elif terlist[indvterritory]["guild"] in allies:
                                terstatus += f"\n{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                alliesowned += 1
                                cong.append(f"{indvterritory}: 🔵")
                            else:
                                terstatus += f"\n{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                lostcount += 1
                                cong.append(f"{indvterritory}: 🔴")

                embed.add_field(name=territoryarea,value=terstatus,inline=False)

            ffastatus = ""
            for ter in terlist.values():
                if fallbackmode:
                    try:
                        if ffacheck(ter) and ter["guild"] == "Lux Nova":
                            ownedffas += 1
                            if ffastatus == "":
                                ffastatus = ter['territory'] + ": 🟢"
                            else:
                                ffastatus = ffastatus + f"\n{ter['territory']}: 🟢"
                            cong.append(f"{ter['territory']}: 🟢")
                    except:
                        pass
                else:
                    if ffacheck(ter) and ter["guild"] == "Lux Nova":
                        ownedffas += 1
                        if ffastatus == "":
                            ffastatus = ter['territory'] + ": 🟢"
                        else:
                            ffastatus = ffastatus + f"\n{ter['territory']}: 🟢"
                        cong.append(f"{ter['territory']}: 🟢")
            if ffastatus != "":
                embed.add_field(name="Other",value=ffastatus,inline=False)

            ownedters = f"Claims: {ownedcount}/{ownedcount+lostcount+alliesowned}"
            if alliesowned:
                ownedters += f" Ally Owned Claims: {alliesowned}"
            if lostcount:
                ownedters += f" Missing Claims: {lostcount}"
            if ownedffas:
                ownedters += f" Other: {ownedffas}"
            embed.add_field(name="Territories Overview",value=ownedters,inline=False)

            cong.sort()

            req = "Automated Owned Territory Check."
            embed.set_footer(text=req)

            for id in trackerchannels:
                try:
                    channel = self.bot.get_channel(id)
                    if channel:
                        if cong != lastoutput:
                            await channel.send(embed=embed)

                    if trackerchannels[id]: #if ping feature enabled
                        for server in self.bot.guilds:
                            if channel in server.text_channels:
                                guild = server

                                if lostcount == 0: #reclaimed all
                                    hourpingtracker = 15
                                    resrvtracker = 0
                                elif lostcount > 3: #reserve ping needed
                                    if resrvtracker == 0:
                                        #reserve role id - 692409024133595136
                                        role = discord.utils.get(guild.roles,name="Reserve")
                                        resrvtracker = 1
                                elif hourpingtracker >= 15: #hour has passed since last ping
                                    # if lostcount > 6:
                                    #     #vanguard role id - 665012396854607903
                                    #     # role = discord.utils.get(guild.roles,name="Vanguard")
                                    #     # hourpingtracker = 0
                                    if lostcount > 1:
                                        #guard role id - 718258222716157952
                                        role = discord.utils.get(guild.roles,name="Praetorian Guard")
                                        hourpingtracker = 0
                                else:
                                    hourpingtracker += 1

                                try: #ping needed
                                    alert = f"⚠️ Alert ⚠️: {role.mention} - {lostcount} territories are missing!"
                                    await channel.send(alert)
                                except: #ping not needed
                                    pass

                                lostcrits = [critter for critter in othercrit if terlist[critter]["guild"] != "Lux Nova"]
                                if lostcrits or terlist[hqter]["guild"] != "Lux Nova":
                                    if not resrvtracker:
                                        role = discord.utils.get(guild.roles,name="Reserve")
                                        additional = f"{role.mention} - "
                                    else:
                                        additional = ""

                                    alert = f"⚠️ Alert ⚠️: {additional}Critical territories are missing!" + "\n- " + "\n- ".join(lostcrits)
                                    await channel.send(alert)
                except:
                    embed = discord.Embed(title="Lux Nova - Territory Update Channel Output", color=0xeb1515)

                    embed.add_field(name="Error",value=f"Could not transmit information to a specified channel with ID: {id}.")

                    req = "Automated Owned Territory Check."
                    embed.set_footer(text=req)

                    error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                    ertext = F"```{error}```"

                    await errorchannel.send(embed=embed)
                    await errorchannel.send(ertext)
                    pass

            lastoutput = cong

            settings.update_one({"scope":"global"},{"$set": {"hourpingtracker":hourpingtracker}})
            settings.update_one({"scope":"global"},{"$set": {"resrvtracker":resrvtracker}})
            terupdateerr = False

        except:

            if terupdateerr == False:
                terupdateerr = True

                embed = discord.Embed(title="Lux Nova - Continued Territory Status", color=0xeb1515)

                embed.add_field(name="Error",value="Could not fetch territory data. This is likely due to an error with the Wynncraft API.")

                req = "Automated Owned Territory Check."
                embed.set_footer(text=req)

                error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                ertext = F"```{error}```"

                for id in trackerchannels:
                    try:
                        channel = self.bot.get_channel(id)
                        await channel.send(embed=embed)
                    except:
                        pass
                await errorchannel.send(embed=embed)
                await errorchannel.send(ertext)
                pass

        if stuckplayers:
            embed = discord.Embed(title="Playtime Tracker Leftover Players", color=0xeb1515)

            out = "The following player(s) could not be found after logging off. They have now been removed from the playtime tracker."
            for player in stuckplayers:
                out += f"\n- {player}"

            embed.add_field(name="Erroring Players",value=out)

            await errorchannel.send(embed=embed)

            stuckplayers = []

        if nialeftmem or niajoinmem:
            joinoutdata = ""
            leftoutdata = ""

            for uuid in nialeftmem:
                data = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()

                uname = data["data"]["player"]["username"]
                fetuuid = data["data"]["player"]["id"]

                if leftoutdata:
                    leftoutdata += f"\n- {uname} [{fetuuid}]"
                else:
                    leftoutdata = f"- {uname} [{fetuuid}]"

            for uuid in niajoinmem:
                data = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()

                uname = data["data"]["player"]["username"]
                fetuuid = data["data"]["player"]["id"]

                if joinoutdata:
                    joinoutdata += f"\n- {uname} [{fetuuid}]"
                else:
                    joinoutdata = f"- {uname} [{fetuuid}]"

            embed = discord.Embed(title="Nerfuria - Members Change", color=0xce34ad)

            if joinoutdata:
                embed.add_field(name="New Members",value=joinoutdata)
            if leftoutdata:
                embed.add_field(name="Ex-Members",value=leftoutdata)

            req = "Automated Member Tracking"
            embed.set_footer(text=req)

            for id in niaalertchannels:
                try:
                    channel = self.bot.get_channel(id)
                    await channel.send(embed=embed)
                except:
                    embed = discord.Embed(title="Nerfuria - Member Channel Output", color=0xeb1515)

                    embed.add_field(name="Error",value=f"Could not transmit information to a specified channel with ID: {id}.")

                    req = "Automated Member Tracking."
                    embed.set_footer(text=req)

                    error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                    ertext = F"```{error}```"

                    await errorchannel.send(embed=embed)
                    await errorchannel.send(ertext)
                    pass

            nialeftmem = []
            niajoinmem = []

        if lxaleftmem or lxajoinmem:
            joinoutdata = ""
            leftoutdata = ""

            for uuid in lxaleftmem:
                data = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()

                uname = data["data"]["player"]["username"]
                fetuuid = data["data"]["player"]["id"]

                if leftoutdata:
                    leftoutdata += f"\n- {uname} [{fetuuid}]"
                else:
                    leftoutdata = f"- {uname} [{fetuuid}]"

            for uuid in lxajoinmem:
                data = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()

                uname = data["data"]["player"]["username"]
                fetuuid = data["data"]["player"]["id"]

                if joinoutdata:
                    joinoutdata += f"\n- {uname} [{fetuuid}]"
                else:
                    joinoutdata = f"- {uname} [{fetuuid}]"

            embed = discord.Embed(title="Lux Nova - Members Change", color=0xce34ad)

            if joinoutdata:
                embed.add_field(name="New Members",value=joinoutdata)
            if leftoutdata:
                embed.add_field(name="Ex-Members",value=leftoutdata)

            req = "Automated Member Tracking"
            embed.set_footer(text=req)

            for id in lxaalertchannels:
                try:
                    channel = self.bot.get_channel(id)

                    await channel.send(embed=embed)
                except:
                    embed = discord.Embed(title="Lux Nova - Member Channel Output", color=0xeb1515)

                    embed.add_field(name="Error",value=f"Could not transmit information to a specified channel with ID: {id}.")

                    req = "Automated Member Tracking."
                    embed.set_footer(text=req)

                    error = re.sub(r'"(.*)"', "", traceback.format_exc(),1)
                    ertext = F"```{error}```"

                    await errorchannel.send(embed=embed)
                    await errorchannel.send(ertext)
                    pass

            lxaleftmem = []
            lxajoinmem = []

        if infodown["guilds"]:
            if not guildsupdateerr:
                owner = await self.bot.fetch_user(276976462140014593)
                embed = discord.Embed(title="Global - Guild List Status", color=0xeb1515)

                embed.add_field(name="Error",value="Could not fetch guild data. This is likely due to an error with the Wynncraft API.")

                req = "Automated Error Check."
                embed.set_footer(text=req)
                await errorchannel.send(embed=embed)
                guildsupdateerr = True
        if infodown["monthlyxp"]:
            if not monthlyxpupdateerr:
                owner = await self.bot.fetch_user(276976462140014593)
                embed = discord.Embed(title="Lux Nova - XP Contribution Status", color=0xeb1515)

                embed.add_field(name="Error",value="Could not fetch xp contributions data. This is likely due to an error with the Wynncraft API.")

                req = "Automated Error Check."
                embed.set_footer(text=req)
                await errorchannel.send(embed=embed)
                monthlyxpupdateerr = True

        if playtimeerrors:
            for i in playtimeerrors:
                type = i["type"]
                data = str(i["data"])

                with open("error.txt", "w") as file:
                    file.write(data)

                errembed = discord.Embed(title="Playtime Update Error", color=0xeb1515)
                errembed.add_field(name="Error",value=f"A {type} fetching error occurred when acquiring data for playtime tracking.")

                req = "Automated Error Check."
                errembed.set_footer(text=req)
                with open("error.txt", "rb") as file:
                    await errorchannel.send(embed=errembed,file=discord.File(file,"error.txt"))
            playtimeerrors = []

    #check lxa territories
    @commands.command()
    async def lxa(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        updter = requests.get("https://api.wynncraft.com/public_api.php?action=territoryList", params=wynnheader).json()
        terlist = updter["territories"]

        ownedcount = 0
        lostcount = 0
        ownedffas = 0
        alliesowned = 0

        embed = discord.Embed(title="Lux Nova - Territory Status", color=0xa049b8)

        for territoryarea in territories["Lux Nova"]:
            terstatus = ""
            for indvterritory in territories["Lux Nova"][territoryarea]:
                if fallbackmode:
                    try:
                        if terstatus == "":
                            if terlist[indvterritory]["guild"] == "Lux Nova":
                                terstatus = f"{indvterritory}: 🟢"
                                ownedcount += 1
                            elif terlist[indvterritory]["guild"] in allies:
                                terstatus = f"{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                alliesowned += 1
                            else:
                                terstatus = f"{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                lostcount += 1
                        else:
                            if terlist[indvterritory]["guild"] == "Lux Nova":
                                terstatus += f"\n{indvterritory}: 🟢"
                                ownedcount += 1
                            elif terlist[indvterritory]["guild"] in allies:
                                terstatus += f"\n{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                                alliesowned += 1
                            else:
                                terstatus += f"\n{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                                lostcount += 1
                    except:
                        if terstatus == "":
                            terstatus = f"{indvterritory}: Invalid Territory"
                        else:
                            terstatus += f"\n{indvterritory}: Invalid Territory"
                else:
                    if terstatus == "":
                        if terlist[indvterritory]["guild"] == "Lux Nova":
                            terstatus = f"{indvterritory}: 🟢"
                            ownedcount += 1
                        elif terlist[indvterritory]["guild"] in allies:
                            terstatus = f"{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                            alliesowned += 1
                        else:
                            terstatus = f"{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                            lostcount += 1
                    else:
                        if terlist[indvterritory]["guild"] == "Lux Nova":
                            terstatus += f"\n{indvterritory}: 🟢"
                            ownedcount += 1
                        elif terlist[indvterritory]["guild"] in allies:
                            terstatus += f"\n{indvterritory}: 🔵 Owned by: {terlist[indvterritory]['guild']}"
                            alliesowned += 1
                        else:
                            terstatus += f"\n{indvterritory}: 🔴 Owned by: {terlist[indvterritory]['guild']}"
                            lostcount += 1

            embed.add_field(name=territoryarea,value=terstatus,inline=False)

        ffastatus = ""
        for ter in terlist.values():
            if fallbackmode:
                try:
                    if ffacheck(ter) and ter["guild"] == "Lux Nova":
                        ownedffas += 1
                        if ffastatus == "":
                            ffastatus = ter['territory'] + ": 🟢"
                        else:
                            ffastatus = ffastatus + f"\n{ter['territory']}: 🟢"
                except:
                    pass
            else:
                if ffacheck(ter) and ter["guild"] == "Lux Nova":
                    ownedffas += 1
                    if ffastatus == "":
                        ffastatus = ter['territory'] + ": 🟢"
                    else:
                        ffastatus = ffastatus + f"\n{ter['territory']}: 🟢"
        if ffastatus != "":
            embed.add_field(name="Other",value=ffastatus,inline=False)

        ownedters = f"Claims: {ownedcount}/{ownedcount+lostcount+alliesowned}"
        if alliesowned:
            ownedters += f" Ally Owned Claims: {alliesowned}"
        if lostcount:
            ownedters += f" Missing Claims: {lostcount}"
        if ownedffas:
            ownedters += f" Other: {ownedffas}"
        embed.add_field(name="Territories Overview",value=ownedters,inline=False)

        req = "Requested by " + ctx.message.author.name + "."
        embed.set_footer(text=req)

        await ctx.send(embed=embed)

    @commands.command(aliases=['ping'])
    async def pings(self, ctx, polarity, channel=None):
        try:
            await ctx.message.delete()
        except:
            pass
        if ctx.message.author.guild_permissions.manage_guild or ctx.author.id == 276976462140014593:
            try:
                if not channel:
                    chnl = ctx.message.channel
                    id = chnl.id
                else:
                    guild = ctx.message.guild
                    chnl = discord.utils.get(guild.channels, name=channel)
                    id = chnl.id
                if id in trackerchannels or ctx.author.id == 276976462140014593:
                    pl = polarity.lower()

                    if pl == "on" or pl == "true" or pl == "enable":
                        trackerchannels[id] = True
                    elif pl == "off" or pl == "false" or pl == "disable":
                        trackerchannels[id] = False

                    smsg = f'Now set to {trackerchannels[id]} for channel: {chnl.mention} [{id}].'
                    success = discord.Embed(title="Pings Setting Altered", color=0xf5c242)

                    success.add_field(name="Pings Setting", value=smsg, inline=True)

                    req = "Requested by " + ctx.message.author.name + "."
                    success.set_footer(text=req)

                    await ctx.send(embed=success)
                else:
                    wmsg = f'The inputted channel is not currently tracked, please try again with another channel.'
                    warn = discord.Embed(title="Error - Channel Not Tracked", color=0xf5c242)

                    warn.add_field(name="Channel information", value=wmsg, inline=True)

                    req = "Requested by " + ctx.message.author.name + "."
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
            except:
                wmsg = f'An error occured with fetching the inputted channel.'
                warn = discord.Embed(title="Error - Invalid Channel", color=0xf5c242)

                warn.add_field(name="Error", value=wmsg, inline=True)

                req = "Requested by " + ctx.message.author.name + "."
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
        else:
            wmsg = f'You do not have sufficient permissions to use this command.'
            warn = discord.Embed(title="Error - Insufficient Permissions", color=0xf5c242)

            warn.add_field(name="Error", value=wmsg, inline=True)

            req = "Requested by " + ctx.message.author.name + "."
            warn.set_footer(text=req)

            await ctx.send(embed=warn)

        settings.update_one({"scope":"global"},{"$set": {"trackerchannels":str(trackerchannels)}})

    @commands.command()
    async def activity(self, ctx, *guildcheck):
        try:
            await ctx.message.delete()
        except:
            pass

        req = "Requested by " + ctx.message.author.name + "."

        global ratelimitedusers
        userid = ctx.author.id

        if userid in ratelimitedusers:
            currenttime = datetime.now(aus)
            endtime = ratelimitedusers[userid]["endtime"]

            if currenttime >= endtime: #past end
                try:
                    ratelimitedusers.pop(userid)
                except:
                    pass
            else:
                remaining = (endtime-currenttime).total_seconds()

                wmsg = f'You are sending activity commands too often, please try again in {remaining} seconds.'
                warn = discord.Embed(title="Error - User Ratelimited", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return
        else:
            process_ratelimit(userid,"activity")

        global guildlst
        guildsearch = " ".join(guildcheck)

        try:
            guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearch}", params=wynnheader).json()

            members = guildstats["members"]

            total = len(members)
            count = 0

            req = "Please wait, this process may take a few minutes..."
            pmsg = f"0/{total} checks completed: 0.0% done."
            title = f"Guild Activity Progress - {guildsearch}"
            progress = discord.Embed(title=title, color=0xf5c242)

            progress.add_field(name="Checks Completed", value=pmsg, inline=True)
            progress.set_footer(text=req)

            pmessage = await ctx.send(embed=progress)

            memberslst = []
            last = 0

            rankselection = {"OWNER":1,"CHIEF":2,"STRATEGIST":3,"CAPTAIN":4,"RECRUITER":5,"RECRUIT":6}
            revrankselection = {1:"OWNER",2:"CHIEF",3:"STRATEGIST",4:"CAPTAIN",5:"RECRUITER",6:"RECRUIT"}

            for member in members:
                #member add
                username = member["name"]
                rank = member["rank"]
                uuid = member["uuid"]

                memberinfo = requests.get(f"https://api.wynncraft.com/v2/player/{uuid}/stats", params=wynnheader).json()
                joingrab = memberinfo["data"][0]["meta"]["lastJoin"]
                lastjoin = joingrab.split("T")
                lastjoinobj = datetime.strptime(lastjoin[0], "%Y-%m-%d")
                currenttime = datetime.utcnow()
                indays = (currenttime - lastjoinobj).days

                member_data = {"username":username,"rank":rankselection[rank],"daysdif":indays}
                memberslst.append(member_data)

                count += 1

                if (count == last + 20) or (count + 3 > total):
                    #embed update
                    req = "Please wait, this process may take a few minutes..."
                    perc = (count/total)*100
                    pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                    title = f"Guild Activity Progress - {guildsearch}"
                    newprogress = discord.Embed(title=title, color=0xf5c242)

                    newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    newprogress.set_footer(text=req)

                    await pmessage.edit(embed=newprogress)
                    last = count

            await asyncio.sleep(1)
            await pmessage.delete()

            memberslst.sort(key = lambda x: x['username'])
            memberslst.sort(key = lambda x: x["daysdif"],reverse=True)
            memberslst.sort(key = lambda x: x["rank"])

            req = "Requested by " + ctx.message.author.name + "."

            title = f"Guild Activity - {guildsearch}"
            #send message
            embed = discord.Embed(title=title, color=0x6edd67)

            output = {"rank":"","text":""}

            for player in memberslst:
                storedrank = player["rank"]
                rank = revrankselection[storedrank]
                if output["rank"] == rank: #same or lower rank
                    if len(output["text"]) < 950:
                        if player['daysdif'] == 1:
                            output["text"] += f"\n{player['username']} : Last joined 1 day ago."
                        else:
                            output["text"] += f"\n{player['username']} : Last joined {player['daysdif']} days ago."
                    else: #full
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)
                        output = {"rank":rank,"text":""}
                        if player['daysdif'] == 1:
                            output["text"] += f"{player['username']} : Last joined 1 day ago."
                        else:
                            output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
                else: #was higher rank
                    if output["text"]:
                        output["text"] = discord.utils.escape_markdown(output["text"])
                        embed.add_field(name=output["rank"],value=output["text"],inline=False)
                    output = {"rank":rank,"text":""}
                    if player['daysdif'] == 1:
                        output["text"] += f"{player['username']} : Last joined 1 day ago."
                    else:
                        output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
            if output["text"]:
                output["text"] = discord.utils.escape_markdown(output["text"])
                embed.add_field(name=output["rank"],value=output["text"],inline=False)

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

        except:
            if guildsearch.lower() in guildlst:
                guildsearched = guildlst[guildsearch.lower()]
                if "|" in guildsearched:
                    guildspot = guildsearched.split("|")
                    gldpotlst = ""

                    count = 1
                    while count < len(guildspot):
                        if gldpotlst == "":
                            gldpotlst = f"{guildspot[count-1]} - {count}"
                        else:
                            gldpotlst += f"\n{guildspot[count-1]} - {count}"
                        count += 1
                    choosemessage = f'```There are multiple guilds with the prefix: "{guildsearch}". Please respond with the number corresponding to the intended guild, within the next 30 seconds. \n{gldpotlst}```'
                    cmsg = await ctx.send(choosemessage)

                    srvtrack[ctx.guild.id] = (guildspot, ctx.author.id, cmsg, "activity")

                    await asyncio.sleep(30)
                    try:
                        await cmsg.delete()
                        del srvtrack[ctx.guild.id]
                    except:
                        pass
                else:
                    try:
                        guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearched}", params=wynnheader).json()

                        members = guildstats["members"]

                        total = len(members)
                        count = 0

                        req = "Please wait, this process may take a few minutes..."
                        pmsg = f"0/{total} checks completed: 0.0% done."
                        title = f"Guild Activity Progress - {guildsearched}"
                        progress = discord.Embed(title=title, color=0xf5c242)

                        progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                        progress.set_footer(text=req)

                        pmessage = await ctx.send(embed=progress)

                        memberslst = []
                        last = 0

                        rankselection = {"OWNER":1,"CHIEF":2,"STRATEGIST":3,"CAPTAIN":4,"RECRUITER":5,"RECRUIT":6}
                        revrankselection = {1:"OWNER",2:"CHIEF",3:"STRATEGIST",4:"CAPTAIN",5:"RECRUITER",6:"RECRUIT"}

                        for member in members:
                            #member add
                            username = member["name"]
                            rank = member["rank"]
                            uuid = member["uuid"]

                            memberinfo = requests.get(f"https://api.wynncraft.com/v2/player/{uuid}/stats", params=wynnheader).json()
                            joingrab = memberinfo["data"][0]["meta"]["lastJoin"]
                            lastjoin = joingrab.split("T")
                            lastjoinobj = datetime.strptime(lastjoin[0], "%Y-%m-%d")
                            currenttime = datetime.utcnow()
                            indays = (currenttime - lastjoinobj).days

                            member_data = {"username":username,"rank":rankselection[rank],"daysdif":indays}
                            memberslst.append(member_data)

                            count += 1

                            if (count == last + 20) or (count + 3 > total):
                                #embed update
                                req = "Please wait, this process may take a few minutes..."
                                perc = (count/total)*100
                                pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                                title = f"Guild Activity Progress - {guildsearched}"
                                newprogress = discord.Embed(title=title, color=0xf5c242)

                                newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                                newprogress.set_footer(text=req)

                                await pmessage.edit(embed=newprogress)
                                last = count

                        await asyncio.sleep(1)
                        await pmessage.delete()

                        memberslst.sort(key = lambda x: x['username'])
                        memberslst.sort(key = lambda x: x["daysdif"],reverse=True)
                        memberslst.sort(key = lambda x: x["rank"])

                        req = "Requested by " + ctx.message.author.name + "."

                        title = f"Guild Activity - {guildsearched}"
                        #send message
                        embed = discord.Embed(title=title, color=0x6edd67)

                        output = {"rank":"","text":""}

                        for player in memberslst:
                            storedrank = player["rank"]
                            rank = revrankselection[storedrank]
                            if output["rank"] == rank: #same or lower rank
                                if len(output["text"]) < 950:
                                    if player['daysdif'] == 1:
                                        output["text"] += f"\n{player['username']} : Last joined 1 day ago."
                                    else:
                                        output["text"] += f"\n{player['username']} : Last joined {player['daysdif']} days ago."
                                else: #full
                                    if output["text"]:
                                        output["text"] = discord.utils.escape_markdown(output["text"])
                                        embed.add_field(name=output["rank"],value=output["text"],inline=False)
                                    output = {"rank":rank,"text":""}
                                    if player['daysdif'] == 1:
                                        output["text"] += f"{player['username']} : Last joined 1 day ago."
                                    else:
                                        output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
                            else: #was higher rank
                                if output["text"]:
                                    output["text"] = discord.utils.escape_markdown(output["text"])
                                    embed.add_field(name=output["rank"],value=output["text"],inline=False)
                                output = {"rank":rank,"text":""}
                                if player['daysdif'] == 1:
                                    output["text"] += f"{player['username']} : Last joined 1 day ago."
                                else:
                                    output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)

                        embed.set_footer(text=req)

                        await ctx.send(embed=embed)
                    except:
                        pass

            else:
                wmsg = f'No guilds were found with the name/prefix: "{guildsearch}".'
                warn = discord.Embed(title="Error - Guild Not Found", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)

                req = "Requested by " + ctx.message.author.name + "."
                warn.set_footer(text=req)

                await ctx.send(embed=warn)

    @commands.command(aliases=['pt'])
    async def playtime(self, ctx, guild=None, *args):

        req = "Requested by " + ctx.message.author.name + "."

        global ratelimitedusers
        userid = ctx.author.id

        if userid in ratelimitedusers:
            currenttime = datetime.now(aus)
            endtime = ratelimitedusers[userid]["endtime"]

            if currenttime >= endtime: #past end
                try:
                    ratelimitedusers.pop(userid)
                except:
                    pass
            else:
                remaining = round((endtime-currenttime).total_seconds(), 1)

                wmsg = f'You are sending playtime commands too often, please try again in {remaining} seconds.'
                warn = discord.Embed(title="Error - User Ratelimited", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return
        else:
            process_ratelimit(userid,"playtime")

        prefixtoname = {"nia":"Nerfuria","lxa":"Lux Nova","ozi":"First Fleet"}
        if guild:
            glower = guild.lower()
            if glower in prefixtoname:
                guild = prefixtoname[glower]

        if guild == "help":
            req = "Requested by " + ctx.message.author.name + "."

            embed = discord.Embed(title="Playtime Commands", color=0xf5a742)

            embed.add_field(name=".playtime <guild>", value="Displays all playtime of current members.", inline=True)
            embed.add_field(name=".playtime <guild> all", value="Displays all playtime of all members.", inline=True)
            embed.add_field(name=".playtime <guild> <d/w/m/y> <length> <all>", value="Displays all playtime since a given time period.", inline=True)
            embed.add_field(name=".playtime <guild> from <date> <all>", value="Displays all playtime since a specified date.", inline=True)
            embed.add_field(name=".playtime <guild> from <date> to <date> <all>", value="Displays all playtime between two specified dates.", inline=True)
            embed.add_field(name=".playtime help", value="Displays this help menu.", inline=True)

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

        elif guild in guildstocheck:
            tosend = []

            newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}", params=wynnheader).json()
            members = newdata["members"]
            membersuuid = [member["uuid"] for member in members]
            membersuname = [member["name"] for member in members]

            try:
                ptfile, storedplaytime = getdata("playtime.txt")
            except:
                storedplaytime = {}
            try:
                smfile, storedmembers = getdata("members.txt")
            except:
                storedmembers = {}

            guildprefix = newdata["prefix"]

            if args:
                count = 0
                last = 0

                if args[0] == "all":#check all ever
                    data = {}

                    for timeset in storedplaytime:
                        for user in storedplaytime[timeset]:
                            if user["guild"] == guildprefix:
                                uuid = user["uuid"]
                                if uuid not in data:
                                    data[uuid] = user["duration"]
                                else:
                                    data[uuid] += user["duration"]

                        timeday = timeset.split("-")[1]
                        if guildprefix in storedmembers[timeday]:
                            for user in storedmembers[timeday][guildprefix]:
                                if user not in data:
                                    data[user] = 0

                    total = len(data)

                    req = "Please wait, this process may take a few minutes..."
                    pmsg = f"0/{total} checks completed: 0.0% done."
                    title = f"Playtime Check Progress - {guild}"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for uuid in data:
                        try:
                            playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()
                            uname = playerdata["data"]["player"]["username"]
                            if uuid in membersuuid:
                                inguilddata = next((member for member in members if uuid == member["uuid"]),None)
                                rank = rankselection[inguilddata["rank"]]
                            else:
                                rank = rankselection["NOT IN GUILD"]
                            playtime = data[uuid]
                            tosend.append({"name":uname,"total":playtime,"rank":rank})
                        except:
                            print(f"User: {uuid}")
                            pass

                        count += 1

                        if (count == last + 20) or (count + 3 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/len(data))*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - {guild}"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    title = f"{guild} [{guildprefix}] - All Member Playtime"

                elif args[0] in {"h","d","w","m","y"}: #check for time since
                    values = {}

                    currenttime = datetime.now(aus)

                    try:
                        length = int(args[1])
                        if length <= 0:
                            wmsg = 'A negative time length has been inputted. As the bot cannot time travel, no data exists for this time period.'
                            warn = discord.Embed(title="Error - Negative Length", color=0xeb1515)

                            warn.add_field(name="Error", value=wmsg, inline=True)
                            warn.set_footer(text=req)

                            await ctx.send(embed=warn)
                            return
                    except:
                        wmsg = 'Please choose an integer value for the length (.playtime <guild> <h/d/w/m/y> <length>).'
                        warn = discord.Embed(title="Error - Invalid Length Argument", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return

                    if args[0] == "h":
                        startdate = currenttime - timedelta(hours=length)
                    elif args[0] == "d":
                        startdate = currenttime - timedelta(days=length)
                    elif args[0] == "w":
                        startdate = currenttime - timedelta(weeks=length)
                    elif args[0] == "m":
                        startdate = currenttime - relativedelta(months=length)
                    elif args[0] == "y":
                        startdate = currenttime - relativedelta(years=length)

                    try:
                        if args[2] == "all":
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate.replace(tzinfo=None):
                                    for member in check:
                                        if member["guild"] == guildprefix:
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                                timeday = timeset.split("-")[1]
                                for user in storedmembers[timeday][guildprefix]:
                                    if user not in values:
                                        values[user] = 0
                        else:
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate.replace(tzinfo=None):
                                    for member in check:
                                        if member["guild"] == guildprefix:
                                            if member["uuid"] in membersuuid:
                                                if member["uuid"] in values:
                                                    values[member["uuid"]] += member["duration"]
                                                else:
                                                    values[member["uuid"]] = member["duration"]
                    except:
                        for timeset in storedplaytime:
                            check = storedplaytime[timeset]
                            storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                            if storedt > startdate.replace(tzinfo=None):
                                for member in check:
                                    if member["guild"] == guildprefix:
                                        if member["uuid"] in membersuuid:
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                    for user in members:
                        if user["uuid"] not in values:
                            values[user["uuid"]] = 0

                    total = len(values)

                    req = "Please wait, this process may take a few minutes..."
                    pmsg = f"0/{total} checks completed: 0.0% done."
                    title = f"Playtime Check Progress - {guild}"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for member in values:
                        try:
                            playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{member}").json()
                            uname = playerdata["data"]["player"]["username"]
                            if member in membersuuid:
                                inguilddata = next((mem for mem in members if member == mem["uuid"]),None)
                                rank = rankselection[inguilddata["rank"]]
                            else:
                                rank = rankselection["NOT IN GUILD"]
                            tosend.append({"name":uname,"total":values[member],"rank":rank})
                        except:
                            print(f"User: {member}")
                            pass

                        count += 1

                        if (count == last + 20) or (count + 3 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/len(values))*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - {guild}"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    timeconvert = {"h":"hour(s)","d":"day(s)","w":"week(s)","m":"month(s)","y":"year(s)"}
                    title = f"{guild} [{guildprefix}] - Member Playtime (Since {length} {timeconvert[args[0]]})"

                elif args[0] == "from": #check between times
                    values = {}

                    try:
                        currenttime = datetime.now(aus)
                        strstart = args[1]
                        startdate = datetime.strptime(strstart,"%d/%m/%y")
                        try:
                            cont = args[2]
                        except:
                            cont = ""
                        if cont == "to": #end date
                            strend = args[3]
                            enddate = datetime.strptime(strend,"%d/%m/%y")
                        else: #no end date
                            enddate = currenttime.replace(tzinfo=None)
                            strend = (enddate+timedelta(days=1)).strftime("%d/%m/%y")
                    except:
                        wmsg = 'Please input valid date formats [dd/mm/yy] (.playtime <guild> from <startdate> or .playtime <guild> from <startdate> to <enddate>).'
                        warn = discord.Embed(title="Error - Invalid Date Format", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return

                    try:
                        if args[2] == "all" or args[4] == "all":
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate and storedt < enddate:
                                    for member in check:
                                        if member["guild"] == guildprefix:
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                                timeday = timeset.split("-")[1]
                                for user in storedmembers[timeday][guildprefix]:
                                    if user not in values:
                                        values[user] = 0
                        else:
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate and storedt < enddate:
                                    for member in check:
                                        if member["guild"] == guildprefix:
                                            if member["uuid"] in membersuuid:
                                                if member["uuid"] in values:
                                                    values[member["uuid"]] += member["duration"]
                                                else:
                                                    values[member["uuid"]] = member["duration"]
                    except:
                        for timeset in storedplaytime:
                            check = storedplaytime[timeset]
                            storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                            if storedt > startdate and storedt < enddate:
                                for member in check:
                                    if member["guild"] == guildprefix:
                                        if member["uuid"] in membersuuid:
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                    for user in members:
                        if user["uuid"] not in values:
                            values[user["uuid"]] = 0

                    total = len(values)

                    req = "Please wait, this process may take a few minutes..."
                    pmsg = f"0/{total} checks completed: 0.0% done."
                    title = f"Playtime Check Progress - {guild}"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for member in values:
                        try:
                            playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{member}").json()
                            uname = playerdata["data"]["player"]["username"]
                            if member in membersuuid:
                                inguilddata = next((mem for mem in members if member == mem["uuid"]),None)
                                rank = rankselection[inguilddata["rank"]]
                            else:
                                rank = rankselection["NOT IN GUILD"]
                            tosend.append({"name":uname,"total":values[member],"rank":rank})
                        except:
                            print(f"User: {member}")
                            pass

                        count += 1

                        if (count == last + 20) or (count + 3 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/len(values))*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - {guild}"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    title = f"{guild} [{guildprefix}] - Member Playtime (Between {strstart} & {strend})"

                else:#invalid arguments
                    wmsg = 'Please input valid search arguments (.playtime <guild> <(h/d/w/m/y)/from/all>).'
                    warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

            else: #check all current
                count = 0
                last = 0
                playtime = {}
                for timeset in storedplaytime:
                    for data in storedplaytime[timeset]:
                        uuid = data["uuid"]
                        if uuid in membersuuid:
                            if data["guild"] == guildprefix:
                                if uuid in playtime:
                                    playtime[uuid] += data["duration"]
                                else:
                                    playtime[uuid] = data["duration"]

                for member in members:
                    if not member["uuid"] in playtime:
                        playtime[member["uuid"]] = 0

                total = len(playtime)

                req = "Please wait, this process may take a few minutes..."
                pmsg = f"0/{total} checks completed: 0.0% done."
                title = f"Playtime Check Progress - {guild}"
                progress = discord.Embed(title=title, color=0xf5c242)

                progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                progress.set_footer(text=req)

                pmessage = await ctx.send(embed=progress)

                for player in playtime:
                    try:
                        playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{player}").json()
                        uname = playerdata["data"]["player"]["username"]
                        data = next(dataset for dataset in members if dataset["uuid"] == player)
                        rank = rankselection[data["rank"]]
                        tosend.append({"name":uname,"total":playtime[player],"rank":rank})
                    except:
                        print(f"User: {player}")
                        pass

                    count += 1

                    if (count == last + 20) or (count + 3 > total):
                        #embed update
                        req = "Please wait, this process may take a few minutes..."
                        perc = (count/len(playtime))*100
                        pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                        title = f"Playtime Check Progress - {guild}"
                        newprogress = discord.Embed(title=title, color=0xf5c242)

                        newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                        newprogress.set_footer(text=req)

                        await pmessage.edit(embed=newprogress)
                        last = count

                title = f"{guild} [{guildprefix}] - Current Member Playtime"

            await asyncio.sleep(1)
            await pmessage.delete()

            tosend.sort(key = lambda x: x['name'])
            tosend.sort(key = lambda x: x["total"],reverse=True)
            tosend.sort(key = lambda x: x["rank"])

            secembedlim = 5000

            #send message
            embed = discord.Embed(title=title, color=0x6edd67)

            if tosend:
                allstring = "".join(str(val) for val in [[player[a] for a in player] for player in tosend])
                subtotallen = 0
                totallen = len(allstring + " " * 6 * len(tosend))
                if totallen > secembedlim:
                    secembed = discord.Embed(title=f"{title} (cont.)", color=0x6edd67)
                    cleared = False

                output = {"rank":"","text":""}

                for player in tosend:
                    storedrank = player["rank"]
                    rank = revrankselection[storedrank]
                    playtime = player["total"]
                    if len(str(playtime)) > 3:
                        playtime = '{:,}'.format(playtime).replace(","," ")
                    statement = f"\n{player['name']} : {playtime} minutes"
                    if subtotallen > secembedlim:
                        if not cleared:
                            if output["text"]:
                                output["text"] = discord.utils.escape_markdown(output["text"])
                                embed.add_field(name=output["rank"],value=output["text"],inline=False)
                            subtotallen += len(output["text"])
                            output = {"rank":rank,"text":""}
                            cleared = True

                        if output["rank"] == rank: #same or lower rank
                            if len(output["text"]) < 950:
                                output["text"] += statement
                            else: #full
                                if output["text"]:
                                    output["text"] = discord.utils.escape_markdown(output["text"])
                                    secembed.add_field(name=output["rank"],value=output["text"],inline=False)
                                subtotallen += len(output["text"])
                                output = {"rank":rank,"text":""}
                                output["text"] += statement
                        else: #was higher rank
                            if output["text"]:
                                output["text"] = discord.utils.escape_markdown(output["text"])
                                secembed.add_field(name=output["rank"],value=output["text"],inline=False)
                            subtotallen += len(output["text"])
                            output = {"rank":rank,"text":""}
                            output["text"] += statement
                    else:
                        if output["rank"] == rank: #same or lower rank
                            if len(output["text"]) < 950:
                                output["text"] += statement
                            else: #full
                                if output["text"]:
                                    output["text"] = discord.utils.escape_markdown(output["text"])
                                    embed.add_field(name=output["rank"],value=output["text"],inline=False)
                                subtotallen += len(output["text"])
                                output = {"rank":rank,"text":""}
                                output["text"] += statement
                        else: #was higher rank
                            if output["text"]:
                                output["text"] = discord.utils.escape_markdown(output["text"])
                                embed.add_field(name=output["rank"],value=output["text"],inline=False)
                            subtotallen += len(output["text"])
                            output = {"rank":rank,"text":""}
                            output["text"] += statement
            else:
                output = {"rank":"Error","text":"No data was found for playtime during this time period."}

            if output["text"] != "No data was found for playtime during this time period.":
                output["text"] = discord.utils.escape_markdown(output["text"])

                if subtotallen > secembedlim:
                    secembed.add_field(name=output["rank"],value=output["text"],inline=False)
                else:
                    embed.add_field(name=output["rank"],value=output["text"],inline=False)

            req = "Requested by " + ctx.message.author.name + "."

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

            if subtotallen > secembedlim:
                secembed.set_footer(text=req)
                await ctx.send(embed=secembed)

        else:
            req = "Requested by " + ctx.message.author.name + "."

            wmsg = 'Please input a valid guild (.playtime <guild> <(h/d/w/m/y)/from/all>).'
            warn = discord.Embed(title="Error - Invalid Guild Argument", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)

    @commands.command(aliases=['ppt']) #lxa exclusive
    async def pplaytime(self, ctx, user=None, *args):
        req = "Requested by " + ctx.message.author.name + "."

        if user == "help":
            embed = discord.Embed(title="Player Playtime Commands", color=0xf5a742)

            embed.add_field(name=".pplaytime <Username/UUID>", value="Displays current total player for an inputted member.", inline=True)
            embed.add_field(name=".pplaytime <Username/UUID> <d/w/m/y> <length>", value="Displays playtime for an inputted member since a given time period.", inline=True)
            embed.add_field(name=".pplaytime <Username/UUID> from <date>", value="Displays playtime for an inputted member since a specified date.", inline=True)
            embed.add_field(name=".pplaytime <Username/UUID> from <date> to <date>", value="Displays playtime for an inputted member between two specified dates.", inline=True)
            embed.add_field(name=".pplaytime help", value="Displays this help menu.", inline=True)

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

        elif user:

            userjson = requests.get(f"https://playerdb.co/api/player/minecraft/{user}").json()

            if userjson["success"] != True:
                search = discord.utils.escape_markdown(user)
                warn = discord.Embed(title="Error - Player Not Found", color=0xff0000)

                warn.add_field(name="Username/UUID", value=search)
                warn.add_field(name="Error", value="No player with this username or UUID was found.")
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return

            uname = userjson["data"]["player"]["username"]
            uuid = userjson["data"]["player"]["id"]

            try:
                ptfile, storedplaytime = getdata("playtime.txt")
            except:
                storedplaytime = {}
            try:
                smfile, storedmembers = getdata("members.txt")
            except:
                storedmembers = {}

            totalmins = 0
            limitingguild = "LXA"

            if args:
                if args[0] in {"h","d","w","m","y"}:

                    currenttime = datetime.now(aus)

                    try:
                        length = int(args[1])
                        if length <= 0:
                            wmsg = 'A negative time length has been inputted. As the bot cannot time travel, no data exists for this time period.'
                            warn = discord.Embed(title="Error - Negative Length", color=0xeb1515)

                            warn.add_field(name="Error", value=wmsg, inline=True)
                            warn.set_footer(text=req)

                            await ctx.send(embed=warn)
                            return
                    except:
                        wmsg = 'Please choose an integer value for the length (.pplaytime <Username/UUID> <h/d/w/m/y> <length>).'
                        warn = discord.Embed(title="Error - Invalid Length Argument", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return

                    if args[0] == "h":
                        startdate = currenttime - timedelta(hours=length)
                    elif args[0] == "d":
                        startdate = currenttime - timedelta(days=length)
                    elif args[0] == "w":
                        startdate = currenttime - timedelta(weeks=length)
                    elif args[0] == "m":
                        startdate = currenttime - relativedelta(months=length)
                    elif args[0] == "y":
                        startdate = currenttime - relativedelta(years=length)

                    for timeset in storedplaytime:
                        check = storedplaytime[timeset]
                        storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                        if storedt > startdate.replace(tzinfo=None):
                            for member in check:
                                if member["uuid"] == uuid and member["guild"] == limitingguild:
                                    totalmins += member["duration"]

                    timeconvert = {"h":"hour(s)","d":"day(s)","w":"week(s)","m":"month(s)","y":"year(s)"}
                    type = f"Since {length} {timeconvert[args[0]]}"

                elif args[0] == "from":
                    try:
                        currenttime = datetime.now(aus)
                        strstart = args[1]
                        startdate = datetime.strptime(strstart,"%d/%m/%y")
                        try:
                            cont = args[2]
                        except:
                            cont = ""
                        if cont == "to": #end date
                            strend = args[3]
                            enddate = datetime.strptime(strend,"%d/%m/%y")
                        else: #no end date
                            enddate = currenttime.replace(tzinfo=None)
                            strend = (enddate+timedelta(days=1)).strftime("%d/%m/%y")
                    except:
                        wmsg = 'Please input valid date formats [dd/mm/yy] (.pplaytime <Username/UUID> from <startdate> or .pplaytime <Username/UUID> from <startdate> to <enddate>).'
                        warn = discord.Embed(title="Error - Invalid Date Format", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return

                    for timeset in storedplaytime:
                        check = storedplaytime[timeset]
                        storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                        if storedt > startdate and storedt < enddate:
                            for member in check:
                                if member["uuid"] == uuid and member["guild"] == limitingguild:
                                    totalmins += member["duration"]

                    type = f"Between {strstart} & {strend}"

                else:
                    wmsg = 'Please input valid search arguments (.pplaytime <Username/UUID> <(h/d/w/m/y)/from>).'
                    warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return
            else:
                for timeset in storedplaytime:
                    check = storedplaytime[timeset]
                    for member in check:
                        if member["uuid"] == uuid and member["guild"] == limitingguild:
                            totalmins += member["duration"]

                type = "Total Current"

            #send message
            title = "Individual Playtime Checker"
            embed = discord.Embed(title=title, color=0x6edd67)
            search = discord.utils.escape_markdown(user)

            embed.add_field(name="Inputted Username/UUID", value=search, inline=False)
            embed.add_field(name="Timespan", value=type, inline=True)
            embed.add_field(name="Playtime (in minutes)",value=totalmins, inline=True)

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

        else:
            req = "Requested by " + ctx.message.author.name + "."

            wmsg = 'Please input a player username or UUID (.pplaytime <Username/UUID> <(h/d/w/m/y)/from>).'
            warn = discord.Embed(title="Error - Invalid Player Argument", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)

    @commands.command()
    async def members(self, ctx, *guildcheck):
        try:
            await ctx.message.delete()
        except:
            pass

        req = "Requested by " + ctx.message.author.name + "."

        global guildlst
        guildsearch = " ".join(guildcheck)

        if not guildsearch:

            wmsg = 'Please input a valid guild (.members <guild>).'
            warn = discord.Embed(title="Error - Invalid Guild Argument", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)
            return

        try:
            guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearch}", params=wynnheader).json()

            members = guildstats["members"]

            memlist = [{"name":mem["name"],"uuid":mem["uuid"],"rank":mem["rank"]} for mem in members]
            title = f"Guild Members List - {guildsearch}"

        except:
            if guildsearch.lower() in guildlst:
                guildsearched = guildlst[guildsearch.lower()]
                if "|" in guildsearched:
                    guildspot = guildsearched.split("|")
                    gldpotlst = ""

                    count = 1
                    while count < len(guildspot):
                        if gldpotlst == "":
                            gldpotlst = f"{guildspot[count-1]} - {count}"
                        else:
                            gldpotlst += f"\n{guildspot[count-1]} - {count}"
                        count += 1
                    choosemessage = f'```There are multiple guilds with the prefix: "{guildsearch}". Please respond with the number corresponding to the intended guild, within the next 30 seconds. \n{gldpotlst}```'
                    cmsg = await ctx.send(choosemessage)

                    srvtrack[ctx.guild.id] = (guildspot, ctx.author.id, cmsg, "memlist")

                    await asyncio.sleep(30)
                    try:
                        await cmsg.delete()
                        del srvtrack[ctx.guild.id]
                    except:
                        pass
                    return
                else:
                    guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearched}", params=wynnheader).json()

                    members = guildstats["members"]

                    memlist = [{"name":mem["name"],"uuid":mem["uuid"],"rank":mem["rank"]} for mem in members]
                    title = f"Guild Members List - {guildsearched}"

        memlist.sort(key = lambda x: x['name'].lower())
        memlist.sort(key = lambda x: rankselection[x["rank"]])

        #send message
        embed = discord.Embed(title=title, color=0x6edd67)

        if memlist:
            output = {"rank":"","text":""}

            for player in memlist:
                rank = player["rank"]
                uname = discord.utils.escape_markdown(player["name"])
                uuid = player["uuid"]
                statement = f"\n{uname} - [*{uuid}*]"
                if output["rank"] == rank: #same or lower rank
                    if len(output["text"]) < 950:
                        output["text"] += statement
                    else: #full
                        if output["text"]:
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)
                        output = {"rank":rank,"text":""}
                        output["text"] += statement
                else: #was higher rank
                    if output["text"]:
                        embed.add_field(name=output["rank"],value=output["text"],inline=False)
                    output = {"rank":rank,"text":""}
                    output["text"] += statement
        else:
            output = {"rank":"Error","text":"No data was found for this guild's members."}

        if output["text"]:
            embed.add_field(name=output["rank"],value=output["text"],inline=False)

        embed.set_footer(text=req)

        await ctx.send(embed=embed)

    @commands.command()
    async def online(self, ctx, *guildcheck):
        try:
            await ctx.message.delete()
        except:
            pass

        req = "Requested by " + ctx.message.author.name + "."

        global guildlst
        guildsearch = " ".join(guildcheck)

        if not guildsearch:

            wmsg = 'Please input a valid guild (.online <guild>).'
            warn = discord.Embed(title="Error - Invalid Guild Argument", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)
            return

        try:
            guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearch}", params=wynnheader).json()

            members = guildstats["members"]

            memberlist = [{"name":mem["name"],"uuid":mem["uuid"],"rank":mem["rank"]} for mem in members]

            totalonline = []

            #gets list of all players online
            onlineplayers = requests.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers", params=wynnheader).json()
            for world in onlineplayers:
                if world != "request":
                    totalonline.extend(onlineplayers[world])

            memlist = [{"name":member["name"],"uuid":member["uuid"],"rank":member["rank"]} for member in memberlist if member["name"] in totalonline]

            title = f"Online Members - {guildsearch}"

        except:
            if guildsearch.lower() in guildlst:
                guildsearched = guildlst[guildsearch.lower()]
                if "|" in guildsearched:
                    guildspot = guildsearched.split("|")
                    gldpotlst = ""

                    count = 1
                    while count < len(guildspot):
                        if gldpotlst == "":
                            gldpotlst = f"{guildspot[count-1]} - {count}"
                        else:
                            gldpotlst += f"\n{guildspot[count-1]} - {count}"
                        count += 1
                    choosemessage = f'```There are multiple guilds with the prefix: "{guildsearch}". Please respond with the number corresponding to the intended guild, within the next 30 seconds. \n{gldpotlst}```'
                    cmsg = await ctx.send(choosemessage)

                    srvtrack[ctx.guild.id] = (guildspot, ctx.author.id, cmsg, "onlist")

                    await asyncio.sleep(30)
                    try:
                        await cmsg.delete()
                        del srvtrack[ctx.guild.id]
                    except:
                        pass
                    return
                else:
                    guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guildsearched}", params=wynnheader).json()

                    members = guildstats["members"]

                    memberlist = [{"name":mem["name"],"uuid":mem["uuid"],"rank":mem["rank"]} for mem in members]

                    totalonline = []

                    #gets list of all players online
                    onlineplayers = requests.get("https://api.wynncraft.com/public_api.php?action=onlinePlayers", params=wynnheader).json()
                    for world in onlineplayers:
                        if world != "request":
                            totalonline.extend(onlineplayers[world])

                    memlist = [{"name":member["name"],"uuid":member["uuid"],"rank":member["rank"]} for member in memberlist if member["name"] in totalonline]

                    title = f"Online Members - {guildsearched}"

        memlist.sort(key = lambda x: x['name'].lower())
        memlist.sort(key = lambda x: rankselection[x["rank"]])

        #send message
        embed = discord.Embed(title=title, color=0x6edd67)

        if memlist:
            output = {"rank":"","text":""}

            for player in memlist:
                rank = player["rank"]
                uname = discord.utils.escape_markdown(player["name"])
                uuid = player["uuid"]
                statement = f"\n{uname} - [*{uuid}*]"
                if output["rank"] == rank: #same or lower rank
                    if len(output["text"]) < 950:
                        output["text"] += statement
                    else: #full
                        if output["text"]:
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)
                        output = {"rank":rank,"text":""}
                        output["text"] += statement
                else: #was higher rank
                    if output["text"]:
                        embed.add_field(name=output["rank"],value=output["text"],inline=False)
                    output = {"rank":rank,"text":""}
                    output["text"] += statement
        else:
            output = {"rank":"No Members","text":"No guild members are online currently."}

        if output["text"]:
            embed.add_field(name=output["rank"],value=output["text"],inline=False)

        embed.set_footer(text=req)

        await ctx.send(embed=embed)

    @commands.command()
    async def xp(self, ctx, *args):
        #xp (time arguments/api)
        #data stored in monthlyxp
        uuid2uname = {}
        values = {}

        req = "Requested by " + ctx.message.author.name + "."

        global ratelimitedusers
        userid = ctx.author.id

        if userid in ratelimitedusers:
            currenttime = datetime.now(aus)
            endtime = ratelimitedusers[userid]["endtime"]

            if currenttime >= endtime: #past end
                try:
                    ratelimitedusers.pop(userid)
                except:
                    pass
            else:
                remaining = round((endtime-currenttime).total_seconds(), 1)

                wmsg = f'You are sending xp commands too often, please try again in {remaining} seconds.'
                warn = discord.Embed(title="Error - User Ratelimited", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return
        else:
            process_ratelimit(userid,"xp")

        if args:
            tosend = []

            newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Lux Nova", params=wynnheader).json()
            members = newdata["members"]
            memuuidlist = [member["uuid"] for member in members]

            old = PasteFetch("Stored Guild XP Contributions")
            oldmembers = old["data"]

            if args[0] in {"d","w","m","y"}:

                currenttime = datetime.now(aus)

                try:
                    length = int(args[1])
                    if length <= 0:
                        wmsg = 'A negative time length has been inputted. As the bot cannot time travel, no data exists for this time period.'
                        warn = discord.Embed(title="Error - Negative Length", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return
                except:
                    wmsg = 'Please choose an integer value for the length (.xp <h/d/w/m/y> <length>).'
                    warn = discord.Embed(title="Error - Invalid Length Argument", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

                if args[0] == "d":
                    startdate = currenttime - timedelta(days=length)
                elif args[0] == "w":
                    startdate = currenttime - timedelta(weeks=length)
                elif args[0] == "m":
                    startdate = currenttime - relativedelta(months=length)
                elif args[0] == "y":
                    startdate = currenttime - relativedelta(years=length)

                gained = PasteFetch("Gained Guild XP Contributions")
                gaineddata = gained["data"]

                for check in gaineddata:
                    storedt = datetime.strptime(check["date"],"%d/%m/%y")
                    if storedt > startdate.replace(tzinfo=None):
                        for member in check["data"]:
                            try:
                                if args[2] == "all":
                                    if member["uuid"] in values:
                                        values[member["uuid"]] += member["change"]
                                    else:
                                        values[member["uuid"]] = member["change"]
                                        uuid2uname[member["uuid"]] = member["name"]
                            except:
                                if member["uuid"] in values:
                                    values[member["uuid"]] += member["change"]
                                elif member["uuid"] in memuuidlist:
                                    values[member["uuid"]] = member["change"]
                                    uuid2uname[member["uuid"]] = member["name"]

                for indvmem in members:
                    if indvmem["uuid"] not in values:
                        values[indvmem["uuid"]] = 0
                        uuid2uname[indvmem["uuid"]] = indvmem["name"]

                for member in values:
                    name = uuid2uname[member]
                    if any(mem["uuid"] == member for mem in members):
                        foundmember = next(mem for mem in members if mem["uuid"] == member)
                        rank = rankselection[foundmember["rank"]]
                    else:
                        rank = rankselection["NOT IN GUILD"]
                    tosend.append({"name":name,"contr":values[member],"rank":rank})

                timeconvert = {"d":"day(s)","w":"week(s)","m":"month(s)","y":"year(s)"}
                title = f"Lux Nova [LXA] - Member XP Contributions (Since {length} {timeconvert[args[0]]})"

            elif args[0] == "from":
                try:
                    currenttime = datetime.now(aus)
                    strstart = args[1]
                    startdate = datetime.strptime(strstart,"%d/%m/%y")
                    try:
                        cont = args[2]
                    except:
                        cont = ""
                    if cont == "to": #end date
                        strend = args[3]
                        enddate = datetime.strptime(strend,"%d/%m/%y")
                    else: #no end date
                        enddate = currenttime.replace(tzinfo=None)
                        strend = (enddate+timedelta(days=1)).strftime("%d/%m/%y")
                except:
                    wmsg = 'Please input valid date formats [dd/mm/yy] (.xp from <startdate> or .xp from <startdate> to <enddate>).'
                    warn = discord.Embed(title="Error - Invalid Date Format", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

                gained = PasteFetch("Gained Guild XP Contributions")
                gaineddata = gained["data"]

                for check in gaineddata:
                    storedt = datetime.strptime(check["date"],"%d/%m/%y")
                    if storedt > startdate and storedt < enddate:
                        for member in check["data"]:
                            try:
                                if args[2] == "all":
                                    if member["uuid"] in values:
                                        values[member["uuid"]] += member["change"]
                                    else:
                                        values[member["uuid"]] = member["change"]
                                        uuid2uname[member["uuid"]] = member["name"]
                                elif args[2] == "to":
                                    if args[4] == "all":
                                        if member["uuid"] in values:
                                            values[member["uuid"]] += member["change"]
                                        else:
                                            values[member["uuid"]] = member["change"]
                                            uuid2uname[member["uuid"]] = member["name"]
                            except:
                                if member["uuid"] in values:
                                    values[member["uuid"]] += member["change"]
                                elif member["uuid"] in memuuidlist:
                                    values[member["uuid"]] = member["change"]
                                    uuid2uname[member["uuid"]] = member["name"]

                for indvmem in members:
                    if indvmem["uuid"] not in values:
                        values[indvmem["uuid"]] = 0
                        uuid2uname[indvmem["uuid"]] = indvmem["name"]

                for member in values:
                    if any(mem["uuid"] == member for mem in members):
                        foundmember = next(mem for mem in members if mem["uuid"] == member)
                        rank = rankselection[foundmember["rank"]]
                    else:
                        rank = rankselection["NOT IN GUILD"]
                    name = uuid2uname[member]
                    tosend.append({"name":name,"contr":values[member],"rank":rank})

                title = f"Lux Nova [LXA] - Member XP Contributions (Between {strstart} & {strend})"

            elif args[0] == "api":
                for mem in oldmembers:
                    if any(mem["uuid"] == member["uuid"] for member in members):
                        updater = next((member for member in members if mem["uuid"] == member["uuid"]),None)
                        rank = rankselection[updater["rank"]]
                        if updater["contributed"] > mem["contr"]:
                            tosend.append({"name":updater["name"],"contr":updater["contributed"],"rank":rank})
                        else:
                            tosend.append({"name":updater["name"],"contr":mem["contr"],"rank":rank})

                title = f"Lux Nova [LXA]] - Member XP Contributions (From API)"

            else:
                wmsg = 'Please input valid search arguments (.xp <(h/d/w/m/y)/from/api>).'
                warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                warn.add_field(name="Error", value=wmsg, inline=True)
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return

        else:
            gained = PasteFetch("Gained Guild XP Contributions")
            gaineddata = gained["data"]

            for check in gaineddata:
                for member in check["data"]:
                    if member["uuid"] in values:
                        values[member["uuid"]] += member["change"]
                    else:
                        value[member["uuid"]] = member["change"]
                        uuid2uname[member["uuid"]] = member["name"]

            for indvmem in members:
                if indvmem["uuid"] not in values:
                    values[indvmem["uuid"]] = 0
                    uuid2uname[indvmem["uuid"]] = indvmem["name"]

            for member in values:
                name = uuid2uname[member]
                if any(mem["uuid"] == member for mem in members):
                    foundmember = next(mem for mem in members if mem["uuid"] == member)
                    rank = rankselection[foundmember["rank"]]
                else:
                    rank = rankselection["NOT IN GUILD"]
                tosend.append({"name":name,"contr":values[member],"rank":rank})

            title = f"Lux Nova [LXA] - Member XP Contributions (All Stored Data)"

        tosend.sort(key = lambda x: x['name'])
        tosend.sort(key = lambda x: x["contr"],reverse=True)
        tosend.sort(key = lambda x: x["rank"])

        secembedlim = 5000

        #send message
        embed = discord.Embed(title=title, color=0x6edd67)

        if tosend:
            allstring = "".join(str(val) for val in [[player[a] for a in player] for player in tosend])
            subtotallen = 0
            totallen = len(allstring + " " * 6 * len(tosend))
            if totallen > secembedlim:
                secembed = discord.Embed(title=f"{title} (cont.)", color=0x6edd67)
                cleared = False

            output = {"rank":"","text":""}

            for player in tosend:
                storedrank = player["rank"]
                rank = revrankselection[storedrank]
                xpcontr = '{:,}'.format(player["contr"]).replace(","," ")
                statement = f"\n{player['name']} : {xpcontr} xp"
                if subtotallen > secembedlim:
                    if not cleared:
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)
                        subtotallen += len(output["text"])
                        output = {"rank":rank,"text":""}
                        cleared = True

                    if output["rank"] == rank: #same or lower rank
                        if len(output["text"]) < 950:
                            output["text"] += statement
                        else: #full
                            if output["text"]:
                                output["text"] = discord.utils.escape_markdown(output["text"])
                                secembed.add_field(name=output["rank"],value=output["text"],inline=False)
                            subtotallen += len(output["text"])
                            output = {"rank":rank,"text":""}
                            output["text"] += statement
                    else: #was higher rank
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            secembed.add_field(name=output["rank"],value=output["text"],inline=False)
                        subtotallen += len(output["text"])
                        output = {"rank":rank,"text":""}
                        output["text"] += statement
                else:
                    if output["rank"] == rank: #same or lower rank
                        if len(output["text"]) < 950:
                            output["text"] += statement
                        else: #full
                            if output["text"]:
                                output["text"] = discord.utils.escape_markdown(output["text"])
                                embed.add_field(name=output["rank"],value=output["text"],inline=False)
                            subtotallen += len(output["text"])
                            output = {"rank":rank,"text":""}
                            output["text"] += statement
                    else: #was higher rank
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)
                        subtotallen += len(output["text"])
                        output = {"rank":rank,"text":""}
                        output["text"] += statement

        else:
            output = {"rank":"Error","text":"No data was found for XP gained during this time period."}

        if output["text"]:
            output["text"] = discord.utils.escape_markdown(output["text"])

            if subtotallen > secembedlim:
                secembed.add_field(name=output["rank"],value=output["text"],inline=False)
            else:
                embed.add_field(name=output["rank"],value=output["text"],inline=False)

        embed.set_footer(text=req)

        await ctx.send(embed=embed)

        if subtotallen > secembedlim:
            secembed.set_footer(text=req)
            await ctx.send(embed=secembed)

    @commands.command()
    async def pxp(self, ctx, user=None, *args):
        req = "Requested by " + ctx.message.author.name + "."

        #pxp (username/uuid) (time arguments)
        if user:
            userjson = requests.get(f"https://playerdb.co/api/player/minecraft/{user}").json()

            if userjson["success"] != True:
                search = discord.utils.escape_markdown(user)
                warn = discord.Embed(title="Error - Player Not Found", color=0xff0000)

                warn.add_field(name="Username/UUID", value=search)
                warn.add_field(name="Error", value="No player with this username or UUID was found.")
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return

            newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Lux Nova", params=wynnheader).json()
            members = newdata["members"]
            memuuidlist = [member["uuid"] for member in members]
            uuid = userjson["data"]["player"]["id"]

            if uuid in memuuidlist:
                if args:
                    totalxp = 0

                    old = PasteFetch("Stored Guild XP Contributions")
                    oldmembers = old["data"]

                    if args[0] in {"d","w","m","y"}:

                        currenttime = datetime.now(aus)

                        try:
                            length = int(args[1])
                            if length <= 0:
                                wmsg = 'A negative time length has been inputted. As the bot cannot time travel, no data exists for this time period.'
                                warn = discord.Embed(title="Error - Negative Length", color=0xeb1515)

                                warn.add_field(name="Error", value=wmsg, inline=True)
                                warn.set_footer(text=req)

                                await ctx.send(embed=warn)
                                return
                        except:
                            wmsg = 'Please choose an integer value for the length (.pxp <Username/UUID> <h/d/w/m/y> <length>).'
                            warn = discord.Embed(title="Error - Invalid Length Argument", color=0xeb1515)

                            warn.add_field(name="Error", value=wmsg, inline=True)
                            warn.set_footer(text=req)

                            await ctx.send(embed=warn)
                            return

                        if args[0] == "d":
                            startdate = currenttime - timedelta(days=length)
                        elif args[0] == "w":
                            startdate = currenttime - timedelta(weeks=length)
                        elif args[0] == "m":
                            startdate = currenttime - relativedelta(months=length)
                        elif args[0] == "y":
                            startdate = currenttime - relativedelta(years=length)

                        gained = PasteFetch("Gained Guild XP Contributions")
                        gaineddata = gained["data"]

                        for check in gaineddata:
                            storedt = datetime.strptime(check["date"],"%d/%m/%y")
                            if storedt > startdate.replace(tzinfo=None):
                                for member in check["data"]:
                                    if member["uuid"] == uuid:
                                        totalxp += member["change"]
                                        break

                        timeconvert = {"d":"day(s)","w":"week(s)","m":"month(s)","y":"year(s)"}
                        type = f"Since {length} {timeconvert[args[0]]}"

                    elif args[0] == "from":
                        try:
                            currenttime = datetime.now(aus)
                            strstart = args[1]
                            startdate = datetime.strptime(strstart,"%d/%m/%y")
                            try:
                                cont = args[2]
                            except:
                                cont = ""
                            if cont == "to": #end date
                                strend = args[3]
                                enddate = datetime.strptime(strend,"%d/%m/%y")
                            else: #no end date
                                enddate = currenttime.replace(tzinfo=None)
                                strend = (enddate+timedelta(days=1)).strftime("%d/%m/%y")
                        except:
                            wmsg = 'Please input valid date formats [dd/mm/yy] (.pxp <Username/UUID> from <startdate> or .xp from <startdate> to <enddate>).'
                            warn = discord.Embed(title="Error - Invalid Date Format", color=0xeb1515)

                            warn.add_field(name="Error", value=wmsg, inline=True)
                            warn.set_footer(text=req)

                            await ctx.send(embed=warn)
                            return

                        gained = PasteFetch("Gained Guild XP Contributions")
                        gaineddata = gained["data"]

                        for check in gaineddata:
                            storedt = datetime.strptime(check["date"],"%d/%m/%y")
                            if storedt > startdate and storedt < enddate:
                                for member in check["data"]:
                                    if member["uuid"] == uuid:
                                        totalxp += member["change"]
                                        break

                        type = f"Between {strstart} & {strend}"

                    elif args[0] == "api":
                        pastnames = [set["name"] for set in userjson["data"]["meta"]["name_history"]] #make list of all user past names
                        membernames = [mem["name"] for mem in members] #make list of all guild member names
                        overlap = [name for name in reversed(pastnames) if name in membernames] #find overlap and use data
                        outname = overlap[0]

                        for member in members:
                            if member["name"] == outname:
                                totalxp = member["contributed"]
                                break

                        type = f"From API"

                    else:
                        wmsg = 'Please input valid search arguments (.pxp <Username/UUID> <(h/d/w/m/y)/from/api>).'
                        warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                        warn.add_field(name="Error", value=wmsg, inline=True)
                        warn.set_footer(text=req)

                        await ctx.send(embed=warn)
                        return

                    #send message
                    title = "Individual XP Checker"
                    embed = discord.Embed(title=title, color=0x6edd67)
                    search = discord.utils.escape_markdown(user)

                    embed.add_field(name="Inputted Username/UUID", value=search, inline=False)
                    embed.add_field(name="Timespan", value=type, inline=True)
                    embed.add_field(name="XP Gained",value=totalxp, inline=True)

                    embed.set_footer(text=req)

                    await ctx.send(embed=embed)

                else:
                    wmsg = 'Please input valid search arguments (.pxp <Username/UUID> <(h/d/w/m/y)/from/api>).'
                    warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

            else:
                search = discord.utils.escape_markdown(user)
                warn = discord.Embed(title="Error - Player Not In LXA", color=0xff0000)

                warn.add_field(name="Username/UUID", value=search)
                warn.add_field(name="Error", value="No player with this username or UUID was found in LXA.")
                warn.set_footer(text=req)

                await ctx.send(embed=warn)
                return
        else:
            warn = discord.Embed(title="Error - Input Player", color=0xff0000)

            warn.add_field(name="Error", value="No player was inputted, please try again. .pxp <Username/UUID> <args>")
            warn.set_footer(text=req)

            await ctx.send(embed=warn)
            return

    @commands.command()
    async def fallback(self, ctx, specific=None, change=None):
        global fallbackmode

        if ctx.author.id == 276976462140014593:
            await ctx.message.delete()
            if specific == "territory":
                if change:
                    if fallbackmode["territory"]:
                        fallbackmode["territory"] = False
                    else:
                        fallbackmode["territory"] = True
                    wmsg = f'Toggled fallback mode for territory tracking to {fallbackmode["territory"]}.'
                    warn = discord.Embed(title="Fallback Toggled", color=0xf5c242)

                    warn.add_field(name="Change", value=wmsg, inline=True)
                else:
                    wmsg = f'Fallback mode for territory tracking currently set to {fallbackmode["territory"]}.'
                    warn = discord.Embed(title="Fallback Status", color=0xf5c242)

                    warn.add_field(name="Status", value=wmsg, inline=True)
            elif specific == "sessions":
                return
                if change:
                    if fallbackmode["sessions"]:
                        fallbackmode["sessions"] = False
                    else:
                        fallbackmode["sessions"] = True
                    wmsg = f'Toggled fallback mode for sessions tracking to {fallbackmode["sessions"]}.'
                    warn = discord.Embed(title="Fallback Toggled", color=0xf5c242)

                    warn.add_field(name="Change", value=wmsg, inline=True)
                else:
                    wmsg = f'Fallback mode for sessions tracking currently set to {fallbackmode["sessions"]}.'
                    warn = discord.Embed(title="Fallback Status", color=0xf5c242)

                    warn.add_field(name="Status", value=wmsg, inline=True)
            else: #all
                wmsg = f'Fallback mode set to {fallbackmode["sessions"]} for sessions tracking.\nFallback mode set to {fallbackmode["territory"]} for territory tracking.'
                warn = discord.Embed(title="Fallback Status", color=0xf5c242)

                warn.add_field(name="Status", value=wmsg, inline=True)
            settings.update_one({"scope":"global"},{"$set": {"fallbackmode":fallbackmode}})
            await ctx.send(embed=warn)

    @commands.command()
    async def setnewters(self,ctx, *ters):
        global territories

        if ctx.author.id == 276976462140014593:
            try:
                await ctx.message.delete()
            except:
                pass
            change = " ".join(ters)
            ownterritory = {}
            sections = change.split("|")
            for section in sections:
                values = section.split("-")
                sectiontitle = values[0]
                ters = values[1].split(",")
                ownterritory[sectiontitle] = []
                for ter in ters:
                    ownterritory[sectiontitle].append(ter)

            territories["Lux Nova"] = ownterritory
            settings.update_one({"scope":"global"},{"$set": {"territories":territories}})

            wmsg = f'Set territories value to {territories}.'
            warn = discord.Embed(title="Territories Altered", color=0xf5c242)

            warn.add_field(name="Change", value=wmsg, inline=True)

            await ctx.send(embed=warn)

    @commands.command()
    async def tersupdate(self,ctx):
        global territories

        if ctx.author.id == 276976462140014593:
            try:
                await ctx.message.delete()
            except:
                pass

            settings = db["settings"]
            savesets = list(settings.find())

            territories = savesets[0]["territories"]

            wmsg = f'Updated territories value from database to {territories}.'
            warn = discord.Embed(title="Territories Altered", color=0xf5c242)

            warn.add_field(name="Change", value=wmsg, inline=True)

            await ctx.send(embed=warn)

    @commands.command()
    async def ally(self, ctx, action=None, *guild):
        global allies

        #700551758753300531 parli | 665010122107650078 legate | 852755422183817236 lxa - packwatcherdisc
        roles = [700551758753300531,665010122107650078,852755422183817236]
        if (ctx.author.id == 276976462140014593) or (ctx.guild.id in [664581414817234995,606830291838959626] and any(role for role in roles if role in [mrole.id for mrole in ctx.message.author.roles])):
            try:
                await ctx.message.delete()
            except:
                pass
            req = "Executed by " + ctx.message.author.name + "."
            guildtext = " ".join(guild)

            if not action and not guild: #list allies stored
                if allies:
                    data = '- ' + '\n- '.join(allies)
                else:
                    data = "No allied guilds are stored."
                info = discord.Embed(title="Ally List", color=0xf5c242)

                info.add_field(name="Allies", value=data, inline=True)
                info.set_footer(text=req)

                await ctx.send(embed=info)
            elif action and guild:
                if action == "add":#add guild to list
                    allies.append(guildtext)
                    settings.update_one({"scope":"global"},{"$set": {"allies":allies}})

                    data = f'The guild: "{guildtext}" has been added to the ally list.'
                    info = discord.Embed(title=f"Ally Addition - {guildtext}", color=0xf5c242)

                    info.add_field(name="Status", value=data, inline=True)
                    info.set_footer(text=req)

                    await ctx.send(embed=info)
                elif action == "remove": #remove guild from list
                    try:
                        allies.remove(guildtext)
                        settings.update_one({"scope":"global"},{"$set": {"allies":allies}})
                        data = f'The guild: "{guildtext}" has been removed from the ally list.'
                    except:
                        data = f'The guild: "{guildtext}" is not on the ally list and could not be removed.'

                    info = discord.Embed(title=f"Ally Removal - {guildtext}", color=0xf5c242)

                    info.add_field(name="Status", value=data, inline=True)
                    info.set_footer(text=req)

                    await ctx.send(embed=info)
                elif action == "check": #inform if guild in list
                    if guild in allies:
                        status = "is"
                    else:
                        status = "is not"
                    data = f'The guild "{guildtext}" {status} on the ally list.'
                    info = discord.Embed(title=f"Ally Query - {guildtext}", color=0xf5c242)

                    info.add_field(name="Status", value=data, inline=True)
                    info.set_footer(text=req)

                    await ctx.send(embed=info)
                else:
                    data = f'Invalid request, please input a valid action. (.ally <add/remove/check> <guild>)'
                    info = discord.Embed(title=f"Ally Command", color=0xf5c242)

                    info.add_field(name="Error", value=data, inline=True)
                    info.set_footer(text=req)

                    await ctx.send(embed=info)
            else:
                data = f'Invalid request, please input a guild. (.ally <add/remove/check> <guild>)'
                info = discord.Embed(title=f"Ally Command", color=0xf5c242)

                info.add_field(name="Error", value=data, inline=True)
                info.set_footer(text=req)

                await ctx.send(embed=info)

    @commands.command()
    async def exclusive(self,ctx,*args):

        global exclusiveusers

        if ctx.author.id == 276976462140014593:
            try:
                await ctx.message.delete()
            except:
                pass

            embed = discord.Embed(title="Exclusive Users", color=0xf5c242)

            if args[0] == "add":
                try:
                    userid = args[1]
                    exclusiveusers.append(userid)
                    wmsg = f'Appended user {userid} to exclusive users.'
                    settings.update_one({"scope":"global"},{"$set": {"exclusers":exclusiveusers}})
                except:
                    wmsg = f'Please input a user to append to exclusive users. .exclusive add <User ID>'

            elif args[0] == "list":
                users = ", ".join(exclusiveusers)
                wmsg = f"Current Users in exclusive users: {users}"
            elif args[0] == "remove":
                try:
                    userid = args[1]
                    exclusiveusers.append(userid)
                    wmsg = f'Removed user {userid} from exclusive users.'
                    settings.update_one({"scope":"global"},{"$set": {"exclusers":exclusiveusers}})
                except:
                    wmsg = f'Please input a user to remove from exclusive users. .exclusive remove <User ID>'

            embed.add_field(name="Change", value=wmsg, inline=True)

            await ctx.send(embed=embed)

    @commands.command()
    async def setcritters(self,ctx, *ters):
        global hqter
        global othercrit

        if ctx.author.id == 276976462140014593:
            try:
                await ctx.message.delete()
            except:
                pass

            change = " ".join(ters)
            othercrit = []

            sections = change.split("|")
            hqter = sections[0]
            ters = sections[1].split(",")
            for terr in ters:
                othercrit.append(terr)

            data = {"hq":hqter,"othercrit":othercrit}

            settings.update_one({"scope":"global"},{"$set": {"critter":data}})

            hqmsg = f"Set HQ territory to {hqter}"
            wmsg = f'Set other critical territory to {sections[1]}.'
            warn = discord.Embed(title="Critical Territories Altered", color=0xf5c242)

            warn.add_field(name="HQ",value=hqmsg)
            warn.add_field(name="Other Critical Territories", value=wmsg)

            await ctx.send(embed=warn)

    @commands.command()
    async def crittersupdate(self,ctx):
        global hqter
        global othercrit

        if ctx.author.id == 276976462140014593:
            try:
                await ctx.message.delete()
            except:
                pass

            settings = db["settings"]
            savesets = list(settings.find())

            hqter = savesets[0]["critter"]["hq"]
            othercrit = savesets[0]["critter"]["othercrit"]

            hqmsg = f"Updated HQ territory from database to {hqter}"
            wmsg = f'Updated other critical territory from database to {",".join(othercrit)}.'
            warn = discord.Embed(title="Critical Territories Updated", color=0xf5c242)

            warn.add_field(name="HQ",value=hqmsg)
            warn.add_field(name="Other Critical Territories", value=wmsg)

            await ctx.send(embed=warn)

    @commands.command()
    async def wynndebug(self, ctx):
        if ctx.author.id == 276976462140014593:
            await ctx.message.delete()
            debug = discord.Embed(title="Debug Data", color=0xf5c242)

            infodmsg = f'Sessions Info Down: {infodown["sessionsmain"]}\nBackup Sessions Info Down: {infodown["sessionsbackup"]}\nGuild Info Down: {infodown["guilds"]}\nXP Check Down: {infodown["monthlyxp"]}'
            trackmsg = ""
            for id in trackerchannels:
                channel = self.bot.get_channel(id)
                if trackmsg:
                    trackmsg += f'\n\nChannel: {channel.name} Channel ID: {id} Ping Enabled: {trackerchannels[id]}'
                else:
                    trackmsg = f'Channel: {channel.name} Channel ID: {id} Ping Enabled: {trackerchannels[id]}'
            pingtrackmsg = f'Reserve Pinged: {resrvtracker}\nTime Tracker: {hourpingtracker}'
            fallbackinfo = f"Territory Tracking: {fallbackmode['territory']}\nSessions Tracking: {fallbackmode['sessions']}"
            errorsmsg = f'Territory Track Error Encountered: {terupdateerr}\nPlaytime Track Error Encountered: {sessionsmainupdateerr}\nBackup Playtime Track Error Encountered: {sessionsbackupupdateerr}\nGuild List Track Error Encountered: {guildsupdateerr}\nXP Contributions Track Error Encountered: {monthlyxpupdateerr}'

            sessionsupdmsg1 = f'Temp Sessions Raw:\n{tempsessions}'
            sessionsupdmsg2 = f"Online Players Raw:\n{onlineplyrs}"
            backsessionsupdmsg1 = f"Backup Temp Sessions Raw:\n{backuptempsessions}"
            backsessionsupdmsg2 = f"Backup Online Players Raw:\n{backuponlineplyrs}"

            debug.add_field(name="Info Down", value=infodmsg, inline=True)
            debug.add_field(name="Ping Tracker", value=pingtrackmsg, inline=True)
            debug.add_field(name="Fallback Mode",value=fallbackinfo,inline=True)
            debug.add_field(name="Errors", value=errorsmsg, inline=False)
            debug.add_field(name="Tracker Channels", value=trackmsg, inline=False)

            await ctx.send(embed=debug)
            mainmsg = f"Sessions Updating\n```{sessionsupdmsg1}\n\n{sessionsupdmsg2}```"
            await ctx.send(mainmsg)
            if backsessionsupdmsg1 != "Backup Temp Sessions Raw: {}" and backsessionsupdmsg2 != "Backup Online Players Raw: {}":
                backupmsg = f"Backup Sessions Updating\n```{backsessionsupdmsg1}\n\n{backsessionsupdmsg2}```"
                await ctx.send(backupmsg)

    @commands.Cog.listener()
    async def on_message(self, msg):

        if msg.author.bot == False:
            if msg.guild.id in srvtrack:
                data = srvtrack[msg.guild.id]
                if data[1] == msg.author.id:
                    try:
                        requested = int(msg.content)
                        guild = data[0][(requested-1)]

                        await msg.delete()

                        try:
                            del srvtrack[msg.guild.id]
                        except:
                            pass
                        try:
                            cmsg = data[2]
                            await cmsg.delete()
                        except:
                            pass

                        ctx = await self.bot.get_context(msg)

                        guildstats = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}", params=wynnheader).json()

                        members = guildstats["members"]

                        total = len(members)
                        count = 0

                        req = "Please wait, this process may take a few minutes..."
                        pmsg = f"0/{total} checks completed: 0.0% done."
                        title = f"Guild Activity Progress - {guild}"
                        progress = discord.Embed(title=title, color=0xf5c242)

                        progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                        progress.set_footer(text=req)

                        pmessage = await ctx.send(embed=progress)

                        memberslst = []
                        last = 0

                        rankselection = {"OWNER":1,"CHIEF":2,"STRATEGIST":3,"CAPTAIN":4,"RECRUITER":5,"RECRUIT":6}
                        revrankselection = {1:"OWNER",2:"CHIEF",3:"STRATEGIST",4:"CAPTAIN",5:"RECRUITER",6:"RECRUIT"}

                        for member in members:
                            #member add
                            username = member["name"]
                            rank = member["rank"]
                            uuid = member["uuid"]

                            memberinfo = requests.get(f"https://api.wynncraft.com/v2/player/{uuid}/stats", params=wynnheader).json()
                            joingrab = memberinfo["data"][0]["meta"]["lastJoin"]
                            lastjoin = joingrab.split("T")
                            lastjoinobj = datetime.strptime(lastjoin[0], "%Y-%m-%d")
                            currenttime = datetime.utcnow()
                            indays = (currenttime - lastjoinobj).days

                            member_data = {"username":username,"rank":rankselection[rank],"daysdif":indays}
                            memberslst.append(member_data)

                            count += 1

                            if (count == last + 20) or (count + 3 > total):
                                #embed update
                                req = "Please wait, this process may take a few minutes..."
                                perc = (count/total)*100
                                pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                                title = f"Guild Activity Progress - {guild}"
                                newprogress = discord.Embed(title=title, color=0xf5c242)

                                newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                                newprogress.set_footer(text=req)

                                await pmessage.edit(embed=newprogress)
                                last = count

                        await asyncio.sleep(1)
                        await pmessage.delete()

                        memberslst.sort(key = lambda x: x['username'])
                        memberslst.sort(key = lambda x: x["daysdif"],reverse=True)
                        memberslst.sort(key = lambda x: x["rank"])

                        req = "Requested by " + ctx.message.author.name + "."

                        title = f"Guild Activity - {guild}"
                        #send message
                        embed = discord.Embed(title=title, color=0x6edd67)

                        output = {"rank":"","text":""}

                        for player in memberslst:
                            storedrank = player["rank"]
                            rank = revrankselection[storedrank]
                            if output["rank"] == rank: #same or lower rank
                                if len(output["text"]) < 950:
                                    if player['daysdif'] == 1:
                                        output["text"] += f"\n{player['username']} : Last joined 1 day ago."
                                    else:
                                        output["text"] += f"\n{player['username']} : Last joined {player['daysdif']} days ago."
                                else: #full
                                    if output["text"]:
                                        output["text"] = discord.utils.escape_markdown(output["text"])
                                        embed.add_field(name=output["rank"],value=output["text"],inline=False)
                                    output = {"rank":rank,"text":""}
                                    if player['daysdif'] == 1:
                                        output["text"] += f"{player['username']} : Last joined 1 day ago."
                                    else:
                                        output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
                            else: #was higher rank
                                if output["text"]:
                                    output["text"] = discord.utils.escape_markdown(output["text"])
                                    embed.add_field(name=output["rank"],value=output["text"],inline=False)
                                output = {"rank":rank,"text":""}
                                if player['daysdif'] == 1:
                                    output["text"] += f"{player['username']} : Last joined 1 day ago."
                                else:
                                    output["text"] += f"{player['username']} : Last joined {player['daysdif']} days ago."
                        if output["text"]:
                            output["text"] = discord.utils.escape_markdown(output["text"])
                            embed.add_field(name=output["rank"],value=output["text"],inline=False)

                        embed.set_footer(text=req)

                        await ctx.send(embed=embed)
                    except:
                        pass
            elif msg.content.startswith("!ffa") or msg.content.startswith("!claims"):
                user = msg.author
                guild = msg.guild
                alwroles = [810322257762844743,732976599217078304,700551758753300531,907492562783318066,665010122107650078] #triarii, centurion, parli, trial legate, legate
                req = "Sent by " + user.name + "."

                await msg.delete()

                if isinstance(msg.channel, discord.channel.DMChannel):
                    wmsg = 'You cannot use the this command in DMs, please run the command in a server.'
                    req = "If this error continues to occur and the current channel is not a DM, please ping or message Wolfdragon24#1477."
                    warn = discord.Embed(title="Warring Alert", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=False)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

                if ((guild.id == 664581414817234995) and any(role for role in alwroles if role in [mrole.id for mrole in user.roles])) or user.id == 276976462140014593: #if server is lxa discord and roles are in allowed

                    if msg.content.startswith("!ffa"):
                        type = "FFAs"
                    elif msg.content.startswith("!claims"):
                        type = "Claims"

                    if msg.content in ["!ffa","!ffa "] or msg.content in ["!claims","!claims "]:
                        outtext = "No additional information provided."
                    else:
                        outtext = (msg.content).replace("!ffa ","").replace("!claims ","")

                    info = discord.Embed(title=f"Warring Alert", color=0xf5c242)

                    info.add_field(name="Type",value=type,inline=False)
                    info.add_field(name="Message", value=outtext, inline=False)

                    info.set_footer(text=req)

                    try:
                        wardisc = self.bot.get_channel(665012747532238849)
                        if type == "FFAs":
                            ping = guild.get_role(718258222716157952)
                        elif type == "Claims":
                            ping = guild.get_role(665012396854607903)
                        text = ping.mention

                        await wardisc.send(embed=info,content=text)
                    except:
                        pass
                    try:
                        traincamp = self.bot.get_channel(711664781177651240)
                        ping = guild.get_role(711664607814484019)
                        text = ping.mention

                        await traincamp.send(embed=info,content=text)
                    except:
                        pass
                else:
                    wmsg = 'You do not have permission to use this command, usage is restricted to Triarius+.'
                    warn = discord.Embed(title="Warring Alert", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)

def setup(bot):
    bot.add_cog(WynnModule(bot))

#repeated update loops
loadplaytimeupd.start()
loadgldupdt.start()
loadguildxpupdt.start()
