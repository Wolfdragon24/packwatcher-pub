#import
import discord
import requests
import os
import asyncio
import json
import re
import datetime
import time
import string
import ast
import calendar
import copy
import dateutil
import base64

from discord.ext import commands, tasks
from pymongo import MongoClient
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from discord.ext.tasks import loop
from concurrent.futures import ThreadPoolExecutor
from pytz import timezone
from github import Github

#paste.ee setup
dkey = ""
ukey = ""
key = ""
headers = {'X-Auth-Token': ukey}

ptdkey = ""
ptukey = ""
ptkey = ""
ptheaders = {'X-Auth-Token': ptukey}

#github repo setup
githubpat = ""
g = Github(githubpat)
repo = g.get_user().get_repo("packwatcher-data")

wynnheader = {"apikey":""}

aus = timezone("Australia/Sydney")

storedchanging = {}
storedplaytime = {}
storedmembers = {}
changingcounter = 0

rankselection = {"OWNER":1,"CHIEF":2,"STRATEGIST":3,"CAPTAIN":4,"RECRUITER":5,"RECRUIT":6,"NOT IN GUILD":7}
revrankselection = {1:"OWNER",2:"CHIEF",3:"STRATEGIST",4:"CAPTAIN",5:"RECRUITER",6:"RECRUIT",7:"NOT IN GUILD"}

def getindex(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

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
    loaded = json.loads(pastedata.replace("\'","\""))
    data = loaded["paste"]["sections"][0]["contents"]
    try:
        data = json.loads(data)
    except:
        data = ast.literal_eval(data)
    return data

def PtGetKey(title):
    pastelst = requests.get("https://api.paste.ee/v1/pastes", headers=ptheaders).json()
    for paste in pastelst["data"]:
        if paste["description"] == title:
            return paste["id"]

    payload = {"description":title, "expiration":"31536000", "sections":[{"contents":"{}"}]}
    send = requests.post("https://api.paste.ee/v1/pastes",json=payload,headers=ptheaders).json()
    return send["id"]

def PtPasteFetch(title):
    key = PtGetKey(title)

    pastedata = requests.get(f"https://api.paste.ee/v1/pastes/{key}", headers=ptheaders).text
    loaded = json.loads(pastedata.replace("\'","\""))
    data = loaded["paste"]["sections"][0]["contents"]
    try:
        data = json.loads(data)
    except:
        data = ast.literal_eval(data)
    return data

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

#reference api when checking current
#Stored Guild Xp Contributions - Total since last save (stored data)
#Gained Guild XP Contributions - Change since stored vs current

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

    newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Nerfuria", params=wynnheader).json()
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
            workingdata = {"name":member["name"],"uuid":member["uuid"],"contr":member["contributed"]}
            old["data"].append(workingdata)

        if workingdata["contr"] < member["contributed"]:
            change = member["contributed"] - workingdata["contr"]
            workingdata["contr"] = member["contributed"]

            toupdatelst.append({"name":workingdata["name"],"uuid":workingdata["uuid"],"change":change})
        elif workingdata["contr"] > member["contributed"]:
            change = workingdata["contr"] - member["contributed"]
            #workingdata["contr"]

            #toupdatelst.append({"name":workingdata["name"],"uuid":workingdata["uuid"],"change":change})
        elif workingdata["contr"] == member["contributed"]:
            total = 0
            for timeset in gained["data"]:
                for playerid in timeset["data"]:
                    if playerid["name"] == member["name"]:
                        total += playerid["change"]
            if total != workingdata["contr"]:
                change = workingdata["contr"] - total
                #toupdatelst.append({"name":workingdata["name"],"uuid":workingdata["uuid"],"change":change})

    gained["data"].append({"date":conglodata,"data":toupdatelst})
    old["timestamp"] = conglodata

    pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{gkey}", headers=headers).json()
    pastedel = requests.delete(f"https://api.paste.ee/v1/pastes/{skey}", headers=headers).json()

    gainedpayload = {"description":"Gained Guild XP Contributions", "expiration":"31536000", "sections":[{"contents":str(gained).replace("\'","\"")}]}
    gainedpaste = requests.post("https://api.paste.ee/v1/pastes", json=gainedpayload, headers=headers)
    storedpayload = {"description":"Stored Guild XP Contributions", "expiration":"31536000", "sections":[{"contents":str(old).replace("\'","\"")}]}
    storedpastecr = requests.post("https://api.paste.ee/v1/pastes", json=storedpayload, headers=headers)

@loop(minutes=10)
async def loadguildxpupdt():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), GuildXPContrUpdate)
    except:
        raise

class NiaModule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nia(self, ctx, checktype=None,*args):
        try:
            await ctx.message.delete()
        except:
            pass

        req = "Requested by " + ctx.message.author.name + "."

        #xp commands
        if checktype == "xp":
            tosend = []

            newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Nerfuria", params=wynnheader).json()
            members = newdata["members"]
            memuuidlist = [member["uuid"] for member in members]

            old = PasteFetch("Stored Guild XP Contributions")
            oldmembers = old["data"]

            if args:
                if args[0] == "all":#check all ever
                    gained = PasteFetch("Gained Guild XP Contributions")
                    gaineddata = gained["data"]

                    values = {}
                    uuid2uname = {}

                    for check in gaineddata:
                        for member in check["data"]:
                            if member["uuid"] in values:
                                values[member["uuid"]] += member["change"]
                            else:
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

                    title = f"Nerfuria [Nia] - Total XP Contributions"
                elif args[0] in {"d","w","m","y"}: #check for time since

                    values = {}
                    uuid2uname = {}

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
                        wmsg = 'Please choose an integer value for the length (.nia xp <d/w/m/y> <length>).'
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

                    timeconvert = {"d":"days","w":"weeks","m":"months","y":"years"}
                    title = f"Nerfuria [Nia] - XP Contributions (Since {length} {timeconvert[args[0]]})"

                elif args[0] == "from": #check between times
                    uuid2uname = {}
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
                        wmsg = 'Please input valid date formats [dd/mm/yy] (.nia xp from <startdate> or .nia xp from <startdate> to <enddate>).'
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
                    title = f"Nerfuria [Nia] - XP Contributions (Between {strstart} & {strend})"

                elif args[0] == "api":
                    for mem in oldmembers:
                        if any(mem["uuid"] == member["uuid"] for member in members):
                            updater = next((member for member in members if mem["uuid"] == member["uuid"]),None)
                            rank = rankselection[updater["rank"]]
                            if updater["contributed"] > mem["contr"]:
                                tosend.append({"name":updater["name"],"contr":updater["contributed"],"rank":rank})
                            else:
                                tosend.append({"name":updater["name"],"contr":mem["contr"],"rank":rank})

                    title = f"Nerfuria [Nia] - Total API Member XP Contributions"

                else:#invalid arguments
                    wmsg = 'Please input valid search arguments (.nia xp <(d/w/m/y)/from/all>).'
                    warn = discord.Embed(title="Error - Invalid Query Argument", color=0xeb1515)

                    warn.add_field(name="Error", value=wmsg, inline=True)
                    warn.set_footer(text=req)

                    await ctx.send(embed=warn)
                    return

            else: #check all current
                gained = PasteFetch("Gained Guild XP Contributions")
                gaineddata = gained["data"]

                values = {}
                uuid2uname = {}

                for check in gaineddata:
                    for member in check["data"]:
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

                title = f"Nerfuria [Nia] - Total Current Member XP Contributions"

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

        #playtime commands
        elif checktype == "playtime" or checktype == "pt":
            tosend = []

            newdata = requests.get(f"https://api.wynncraft.com/public_api.php?action=guildStats&command=Nerfuria", params=wynnheader).json()
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

            storedchanging = PtPasteFetch("Playtime Change Data") #{}

            if args:
                count = 0
                last = 0

                if args[0] == "all":#check all ever
                    data = {}

                    for timeset in storedplaytime:
                        for user in storedplaytime[timeset]:
                            if user["guild"] == "Nia":
                                uuid = user["uuid"]
                                if uuid not in data:
                                    data[uuid] = user["duration"]
                                else:
                                    data[uuid] += user["duration"]

                        timeday = timeset.split("-")[1]
                        for user in storedmembers[timeday]["Nia"]:
                            if user not in data:
                                data[user] = 0

                    total = len(data)

                    req = "Please wait, this process may take a few minutes..."
                    pmsg = f"0/{total} checks completed: 0.0% done."
                    title = f"Playtime Check Progress - Nerfuria"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for uuid in data:
                        playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{uuid}").json()
                        uname = playerdata["data"]["player"]["username"]
                        if uuid in membersuuid:
                            inguilddata = next((member for member in members if uuid == member["uuid"]),None)
                            rank = rankselection[inguilddata["rank"]]
                        else:
                            rank = rankselection["NOT IN GUILD"]
                        playtime = data[uuid]
                        tosend.append({"name":uname,"total":playtime,"rank":rank})

                        count += 1

                        if (count == last + 10) or (count + 5 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/total)*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - Nerfuria"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    title = f"Nerfuria [Nia] - All Member Playtime"

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
                        wmsg = 'Please choose an integer value for the length (.nia playtime <h/d/w/m/y> <length>).'
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
                                        if member["guild"] == "Nia":
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                                timeday = timeset.split("-")[1]
                                for user in storedmembers[timeday]["Nia"]:
                                    if user not in values:
                                        values[user] = 0
                        else:
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate.replace(tzinfo=None):
                                    for member in check:
                                        if member["guild"] == "Nia":
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
                                    if member["guild"] == "Nia":
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
                    title = f"Playtime Check Progress - Nerfuria"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for member in values:
                        playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{member}").json()
                        uname = playerdata["data"]["player"]["username"]

                        if member in membersuuid:
                            foundmember = next(mem for mem in members if mem["uuid"] == member)
                            rank = rankselection[foundmember["rank"]]
                        else:
                            rank = rankselection["NOT IN GUILD"]
                        tosend.append({"name":uname,"total":values[member],"rank":rank})

                        count += 1

                        if (count == last + 10) or (count + 5 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/total)*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - Nerfuria"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    timeconvert = {"h":"hours","d":"days","w":"weeks","m":"months","y":"years"}
                    title = f"Nerfuria [Nia] - Member Playtime (Since {length} {timeconvert[args[0]]})"

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
                        wmsg = 'Please input valid date formats [dd/mm/yy] (.nia playtime from <startdate> or .nia playtime from <startdate> to <enddate>).'
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
                                        if member["guild"] == "Nia":
                                            if member["uuid"] in values:
                                                values[member["uuid"]] += member["duration"]
                                            else:
                                                values[member["uuid"]] = member["duration"]

                                timeday = timeset.split("-")[1]
                                for user in storedmembers[timeday]["Nia"]:
                                    if user not in values:
                                        values[user] = 0
                        else:
                            for timeset in storedplaytime:
                                check = storedplaytime[timeset]
                                storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
                                if storedt > startdate and storedt < enddate:
                                    for member in check:
                                        if member["guild"] == "Nia":
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
                                    if member["guild"] == "Nia":
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
                    title = f"Playtime Check Progress - Nerfuria"
                    progress = discord.Embed(title=title, color=0xf5c242)

                    progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                    progress.set_footer(text=req)

                    pmessage = await ctx.send(embed=progress)

                    for member in values:
                        if member in membersuuid:
                            foundmember = next(mem for mem in members if mem["uuid"] == member)
                            rank = rankselection[foundmember["rank"]]
                        else:
                            rank = rankselection["NOT IN GUILD"]

                        playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{member}").json()
                        uname = playerdata["data"]["player"]["username"]

                        tosend.append({"name":uname,"total":values[member],"rank":rank})

                        count += 1

                        if (count == last + 10) or (count + 5 > total):
                            #embed update
                            req = "Please wait, this process may take a few minutes..."
                            perc = (count/total)*100
                            pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                            title = f"Playtime Check Progress - Nerfuria"
                            newprogress = discord.Embed(title=title, color=0xf5c242)

                            newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                            newprogress.set_footer(text=req)

                            await pmessage.edit(embed=newprogress)
                            last = count

                    title = f"Nerfuria [Nia] - Member Playtime (Between {strstart} & {strend})"

                else:#invalid arguments
                    wmsg = 'Please input valid search arguments (.nia playtime <(h/d/w/m/y)/from/all>).'
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
                        if data["guild"] == "Nia":
                            uuid = data["uuid"]
                            if uuid in membersuuid:
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
                title = f"Playtime Check Progress - Nerfuria"
                progress = discord.Embed(title=title, color=0xf5c242)

                progress.add_field(name="Checks Completed", value=pmsg, inline=True)
                progress.set_footer(text=req)

                pmessage = await ctx.send(embed=progress)

                for player in playtime:
                    playerdata = requests.get(f"https://playerdb.co/api/player/minecraft/{player}").json()
                    uname = playerdata["data"]["player"]["username"]
                    try:
                        data = next(dataset for dataset in members if dataset["uuid"] == player)
                        rank = rankselection[data["rank"]]
                        tosend.append({"name":uname,"total":playtime[player],"rank":rank})
                    except:
                        pass

                    count += 1

                    if (count == last + 10) or (count + 5 > total):
                        #embed update
                        req = "Please wait, this process may take a few minutes..."
                        perc = (count/total)*100
                        pmsg = f"{count}/{total} checks completed: {perc:.1f}% done."
                        title = f"Playtime Check Progress - Nerfuria"
                        newprogress = discord.Embed(title=title, color=0xf5c242)

                        newprogress.add_field(name="Checks Completed", value=pmsg, inline=True)
                        newprogress.set_footer(text=req)

                        await pmessage.edit(embed=newprogress)
                        last = count

                title = f"Nerfuria [Nia] - Current Member Playtime"

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

            if output["text"]:
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

        elif checktype == "help":
            req = "Requested by " + ctx.message.author.name + "."

            embed = discord.Embed(title="Nia Check Commands", color=0xf5a742)

            embed.add_field(name=".nia xp", value="Displays all xp gained by current members.", inline=True)
            embed.add_field(name=".nia xp all", value="Displays all xp gained by all members.", inline=True)
            embed.add_field(name=".nia xp <d/w/m/y> <length>", value="Displays all xp gained since a given time period.", inline=True)
            embed.add_field(name=".nia xp from <date>", value="Displays all xp gained since a specified date.", inline=True)
            embed.add_field(name=".nia xp from <date> to <date>", value="Displays all xp gained between two specified dates.", inline=True)
            embed.add_field(name=".nia playtime", value="Displays all playtime of current members.", inline=True)
            embed.add_field(name=".nia playtime all", value="Displays all playtime of all members.", inline=True)
            embed.add_field(name=".nia playtime <d/w/m/y> <length> <all>", value="Displays all playtime since a given time period.", inline=True)
            embed.add_field(name=".nia playtime from <date> <all>", value="Displays all playtime since a specified date.", inline=True)
            embed.add_field(name=".nia playtime from <date> to <date> <all>", value="Displays all playtime between two specified dates.", inline=True)
            embed.add_field(name=".nia help", value="Displays this help menu.", inline=True)

            embed.set_footer(text=req)

            await ctx.send(embed=embed)

        else: #invalid check type
            wmsg = 'Please input a valid check type (.nia <xp/playtime>).'
            warn = discord.Embed(title="Error - Invalid Query Type", color=0xeb1515)

            warn.add_field(name="Error", value=wmsg, inline=True)
            warn.set_footer(text=req)

            await ctx.send(embed=warn)
            return

def setup(bot):
    bot.add_cog(NiaModule(bot))

#repeated update loops

loadguildxpupdt.start()
