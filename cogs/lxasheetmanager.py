import discord
import requests
import datetime
import copy
import json
import time
import base64
import os
import asyncio

from dotenv import dotenv_values
from discord.ext import commands
from discord.ext.tasks import loop
from pytz import timezone
from datetime import datetime, timedelta
from pymongo import MongoClient
from github import Github
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor

config = {
    **dotenv_values(".env"),
    **os.environ,
}

aus = timezone("Australia/Sydney")

#db setup
MONGODB_ADDRESS = config["MONGODB_ADDRESS"]
cluster = MongoClient(MONGODB_ADDRESS)
db = cluster["lxamembersheet"]
collection = db["privdata"]
collection_data = list(collection.find())

GOOGLE_API_KEY = config["GOOGLE_API_KEY"]
OAUTH_REFRESH_TOKEN = config["G_AUTH_REFRESH_TOKEN"]
OAUTH_ACCESS_TOKEN = collection_data[0]["g_access_token"] if "g_access_token" in collection_data[0] else ''
G_CLIENT_ID = config["G_CLIENT_ID"]
G_CLIENT_SECRET = config["G_CLIENT_SECRET"]

SHEETS_GET = "batchGet"
SHEETS_UPDATE = "batchUpdate"
PLAYERDB_ERROR = 'minecraft.api_failure'

GUILD = "Lux Nova"
GUILD_PREFIX = "LXA"
CATEGORIES = {
    "Join Name":"B", "Current Name":"C", "MC UUID":"D",
    "Join Date":"J", "Join Date 2":"L", "Join Date 3":"N",
    "Leave Date":"K", "Leave Date 2":"M", "Leave Date 3":"O",
    "Current Ingame Rank":"W", "Current XP Contribution":"Z",
    "Last Logon":"AF", "Total Activity":"AG", "Last Week Activity":"AH"
}
MEMBER_SHEET_ID = config["MEMBER_SHEET_ID"]
MEMBER_SHEET_NAME = "Member Info Database Project"
BEGIN_ROW = 4

client_app_header = {
    "client_id": G_CLIENT_ID,
    "client_secret": G_CLIENT_SECRET
}
data_type_header = {
    'accept':'application/json',
    'Content-Type':'application/json'
}

member_list = []

# paste.ee setup
paste_dkey = config["PASTEE_DKEY"]
paste_ukey = config["PASTEE_UKEY"]
paste_headers = {'X-Auth-Token': paste_ukey}

# Github setup
github_pat = config["GITHUB_PAT"]
GITHUB_REPO = config["GITHUB_REPO"]
g = Github(github_pat, retry = Retry(total = 10, status_forcelist = (500, 502, 504), backoff_factor = 0.3))
main_repo = g.get_user().get_repo(GITHUB_REPO)

# Wynncraft API setup
WYNNCRAFT_API_KEY = config["WYNNCRAFT_API_KEY"]
wynn_header = {"apikey":WYNNCRAFT_API_KEY}

# UTILITY FUNCTIONS

def get_index(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return None

def get_difference(list_one, list_two):
    old = [item for item in list_one if item not in list_two]
    new = [item for item in list_two if item not in list_one]
    return (old, new)

def get_data(list, key, value):
    for item in list:
        if item[key] == value:
            return item
    return None

def get_row(list, value):
    row = list.index(value) + BEGIN_ROW
    return row

def normalise_string(string):
    return string.lower().capitalize()

def get_guild_stats(guild):
    return f'https://api.wynncraft.com/public_api.php?action=guildStats&command={guild}'

def get_spreadsheet(id, action):
    return f'https://sheets.googleapis.com/v4/spreadsheets/{id}/values:{action}'

def get_playerdb(input):
    return f'https://playerdb.co/api/player/minecraft/{input}'

def new_member_data(username, uuid, date, row):
    data = [
        {
            "range": f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Name']}{row}:{CATEGORIES['MC UUID']}{row}",
            "values": [[username, username, uuid]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Date']}{row}",
            "values": [[date]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current Ingame Rank']}{row}",
            "values": [['Recruit']],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current XP Contribution']}{row}",
            "values": [['0']],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Last Logon']}{row}",
            "values": [[date]],
            "majorDimension": "ROWS"
        }
    ]
    return data

def update_member_data(username, rank, contributions, last_login, tot_playtime, week_playtime, row):
    data = [
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current Name']}{row}",
            "values": [[username]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current Ingame Rank']}{row}",
            "values": [[rank]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current XP Contribution']}{row}",
            "values": [[contributions]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Last Logon']}{row}",
            "values": [[last_login]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Total Activity']}{row}",
            "values": [[tot_playtime]],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Last Week Activity']}{row}",
            "values": [[week_playtime]],
            "majorDimension": "ROWS"
        }
    ]
    return data

def old_member_data(row):
    data = [
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current Ingame Rank']}{row}",
            "values": [['N/A']],
            "majorDimension": "ROWS"
        }
    ]
    return data

def update_member_join_data(join_one, join_two, join_three, row):
    data = []
    if join_one:
        data.append({
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Date']}{row}",
            "values": [[join_one]],
            "majorDimension": "ROWS"
        })
    if join_two:
        data.append({
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Date 2']}{row}",
            "values": [[join_two]],
            "majorDimension": "ROWS"
        })
    if join_three:
        data.append({
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Date 3']}{row}",
            "values": [[join_three]],
            "majorDimension": "ROWS"
        })
    return data

def update_member_leave_data(leave_one, leave_two, leave_three, row):
    data = [
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Current Ingame Rank']}{row}",
            "values": [['N/A']],
            "majorDimension": "ROWS"
        },
        {
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Leave Date']}{row}",
            "values": [[leave_one]],
            "majorDimension": "ROWS"
        }
    ]
    if leave_two:
        data.append({
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Leave Date 2']}{row}",
            "values": [[leave_two]],
            "majorDimension": "ROWS"
        })
    if leave_three:
        data.append({
            "range":f"{MEMBER_SHEET_NAME}!{CATEGORIES['Leave Date 3']}{row}",
            "values": [[leave_three]],
            "majorDimension": "ROWS"
        })
    return data

def update_access_token(token):
    if token:
        collection.update_one({"scope":"global"},{"$set": {"g_access_token":str(token)}})

def refresh_oauth_access_token():
    url = "https://oauth2.googleapis.com/token"
    data = copy.copy(client_app_header)
    data["grant_type"] = "refresh_token"
    data["refresh_token"] = OAUTH_REFRESH_TOKEN

    response = requests.post(url, data=data)

    try:
        response_data = response.json()
        token = response_data["access_token"]
        update_access_token(token)
        return token
    except:
        return None #Create error logging somehow

def execute_google_requests(url, data, headers, type):
    sent = False
    while not sent:
        if type == "POST":
            response = requests.post(url, data=json.dumps(data), headers=headers).json()
        elif type == "GET":
            response = requests.get(url, params=data, headers=headers).json()

        if "error" in response and response["error"]["status"] == "RESOURCE_EXHAUSTED":
            time.sleep(30)
        else:
            return response

def attempt_google_api_interact(url, data, type, url_append=[]):
    global OAUTH_ACCESS_TOKEN

    headers = copy.copy(data_type_header)
    headers["Authorization"] = f"Bearer {OAUTH_ACCESS_TOKEN}"

    url += f"?key={GOOGLE_API_KEY}"

    for item in url_append:
        url += f"&{item}={url_append[item]}"

    response = execute_google_requests(url, data, headers, type)

    if "error" in response:
        if not OAUTH_ACCESS_TOKEN or response["error"]["status"] == "UNAUTHENTICATED":
            OAUTH_ACCESS_TOKEN = refresh_oauth_access_token()

        if not OAUTH_ACCESS_TOKEN:
            return {}
        else:
            headers["Authorization"] = f"Bearer {OAUTH_ACCESS_TOKEN}"

            response = execute_google_requests(url, data, headers, type)

    return response

def GetKey(title):
    pastelst = requests.get("https://api.paste.ee/v1/pastes", headers=paste_headers).json()
    for paste in pastelst["data"]:
        if paste["description"] == title:
            return paste["id"]

    payload = {"description":title, "expiration":"31536000", "sections":[{"contents":"{}"}]}
    send = requests.post("https://api.paste.ee/v1/pastes",json=payload,headers=paste_headers).json()
    return send["id"]

def PasteFetch(title):
    key = GetKey(title)

    pastedata = requests.get(f"https://api.paste.ee/v1/pastes/{key}", headers=paste_headers).text
    loaded = json.loads(pastedata.replace("\"None\"","None").replace("\'","\""))
    data = loaded["paste"]["sections"][0]["contents"]
    try:
        data = json.loads(data)
    except:
        data = ast.literal_eval(data)
    return data

def GithubFetch(filename):
    try:
        data = main_repo.get_contents(filename).decoded_content.decode().replace("'","\"")
        return (main_repo.get_contents(filename), json.loads(data))
    except:
        try:
            ref = main_repo.get_git_ref("heads/main")
            tree = main_repo.get_git_tree(ref.object.sha, recursive='/' in filename).tree
            sha = [x.sha for x in tree if x.path == filename]
            if not sha:
                file = main_repo.create_file(filename, "Automated Data Generation","{}")["content"]
                return(file,{})
            else:
                data = base64.b64decode(main_repo.get_git_blob(sha[0]).content).decode().replace("'","\"")
                return (main_repo.get_git_blob(sha[0]), json.loads(data))
        except:
            return (None, {})

def PlaytimeFetch(member_data):
    playtime_blob, stored_playtime = GithubFetch("playtime.txt")

    members_uuid = [member["uuid"] for member in member_data]

    current_time = datetime.now(aus)

    total_data = {}
    week_data = {}
    last_login = {}

    for timeset in stored_playtime:
        for user in stored_playtime[timeset]:
            if user["guild"] == GUILD_PREFIX:
                uuid = user["uuid"]
                if uuid not in total_data:
                    total_data[uuid] = user["duration"]
                else:
                    total_data[uuid] += user["duration"]

    start_date = current_time - timedelta(weeks=1)

    for timeset in stored_playtime:
        storedt = datetime.strptime(timeset,"%H-%d/%m/%y")
        if storedt > start_date.replace(tzinfo=None):
            for user in stored_playtime[timeset]:
                if user["guild"] == GUILD_PREFIX:
                    uuid = user["uuid"]
                    if uuid in week_data:
                        week_data[uuid] += user["duration"]
                    else:
                        week_data[uuid] = user["duration"]

    for user in member_data:
        if user["uuid"] not in week_data:
            week_data[user["uuid"]] = 0
        if user["uuid"] not in total_data:
            total_data[user["uuid"]] = 0
        member_info = requests.get(f"https://api.wynncraft.com/v2/player/{user['uuid']}/stats", params=wynn_header).json()
        last_join = member_info["data"][0]["meta"]["lastJoin"].split("T")[0]
        last_join_obj = datetime.strptime(last_join, "%Y-%m-%d")
        last_login[user['uuid']] = last_join_obj.strftime("%d/%m/%Y")

    return total_data, week_data, last_login

# SHEET MANAGEMENT FUNCTIONS

def MemberAppend():

    global member_list

    api_data = requests.get(get_guild_stats(GUILD), params=wynn_header).json()
    member_data = api_data["members"]
    new_member_list = [member["uuid"] for member in member_data]

    member_change = get_difference(member_list, new_member_list)
    left = member_change[0]
    joined = member_change[1]

    range_data = f"{MEMBER_SHEET_NAME}!{CATEGORIES['MC UUID']}4:{CATEGORIES['MC UUID']}100"
    sheet_params = {
        "ranges":range_data,
        "majorDimension":"COLUMNS"
    }

    sheets_data = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_GET), sheet_params, "GET")
    user_values = sheets_data["valueRanges"][0]["values"][0]

    range_data = f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Name']}4:{CATEGORIES['Last Week Activity']}100"
    sheet_params = {
        "ranges":range_data,
        "majorDimension":"ROWS"
    }

    sheets_data = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_GET), sheet_params, "GET")
    sheet_values = sheets_data["valueRanges"][0]["values"]
    process_row = BEGIN_ROW + len(user_values)

    for member in joined:
        now_time = datetime.now(aus)
        now_date = now_time.strftime('%d/%m/%Y')
        member_info = get_data(member_data, 'uuid', member)

        if member not in user_values:
            playerdb_member_data = requests.get(get_playerdb(member)).json()

            if playerdb_member_data['code'] == PLAYERDB_ERROR:
                username = member_info['name']
            else:
                username = playerdb_member_data['data']['player']['username']

            try:
                api_join = member_info["joined"].split("T")[0]
                api_join_obj = datetime.strptime(api_join, "%Y-%m-%d")
                join_txt = api_join_obj.strftime("%d/%m/%Y")
            except:
                join_txt = now_date

            update_data = {
                "data":new_member_data(username, member, join_txt, process_row)
            }
            url_append = {"valueInputOption":"RAW"}

            update_sheet = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_UPDATE), update_data, "POST", url_append)

            if update_sheet and "error" in update_sheet:
                print("error occurred for posting request - new member")
                print(update_sheet)
                pass #error logging

            process_row += 1
        else:
            api_join = member_info["joined"].split("T")[0]
            api_join_obj = datetime.strptime(api_join, "%Y-%m-%d")
            api_join_txt = api_join_obj.strftime("%d/%m/%Y")
            row = get_row(user_values, member)

            stored_data = sheet_values[row]
            stored_join_one = stored_data[8]
            stored_left = stored_data[9]
            stored_join_two = stored_data[10]

            if stored_join_one != api_join_txt and stored_left: # new join
                stored_left_obj = datetime.strptime(stored_left, "%d/%m/%Y")
                prev_week = (now_time - timedelta(weeks=1)).replace(tzinfo=None)

                if stored_left_obj < prev_week: # true leave of guild
                    update_data = {
                        "data":update_member_join_data(api_join_txt, stored_join_one, stored_join_two, row)
                    }
                else:
                    update_data = {
                        "data":update_member_leave_data("", None, None, row)
                    }
                url_append = {"valueInputOption":"RAW"}

                update_sheet = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_UPDATE), update_data, "POST", url_append)

                if update_sheet and "error" in update_sheet:
                    print("error occurred for posting request - rejoining member")
                    print(update_sheet)
                    pass #error logging

    for member in left:
        now_time = datetime.now(aus)
        now_date = now_time.strftime('%d/%m/%Y')

        row = get_row(user_values, member)

        stored_data = sheet_values[row]
        stored_left_one = stored_data[9]
        stored_left_two = stored_data[11]

        if stored_left_one and stored_left_one != now_date:
            update_data = {
                "data":update_member_leave_data(now_date, stored_left_one, stored_left_two, row)
            }
        else:
            update_data = {
                "data":update_member_leave_data(now_date, None, None, row)
            }

        url_append = {"valueInputOption":"RAW"}

        update_sheet = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_UPDATE), update_data, "POST", url_append)

        if update_sheet and "error" in update_sheet:
            print("error occurred for posting request - left member")
            print(update_sheet)
            pass #error logging

def MemberUpdate():
    api_data = requests.get(get_guild_stats(GUILD), params=wynn_header).json()
    member_data = api_data["members"]

    range_data = f"{MEMBER_SHEET_NAME}!{CATEGORIES['Join Name']}4:{CATEGORIES['Last Week Activity']}100"
    sheet_params = {
        "ranges":range_data,
        "majorDimension":"ROWS"
    }

    sheets_data = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_GET), sheet_params, "GET")
    sheet_values = sheets_data["valueRanges"][0]["values"]

    total_activity, weekly_activity, last_login = PlaytimeFetch(member_data)

    for row in range(len(sheet_values)):
        stored_data = sheet_values[row]
        stored_uname = stored_data[1]
        stored_uuid = stored_data[2]
        stored_ing_rank = stored_data[21]
        stored_cur_xp = stored_data[24]

        if not stored_uuid:
            break

        current_row = row + BEGIN_ROW

        fetch_data_pos = get_index(member_data, "uuid", stored_uuid)
        if fetch_data_pos != None:
            fetch_data = member_data[fetch_data_pos]
            fetch_uname = fetch_data["name"]
            fetch_ing_rank = normalise_string(fetch_data["rank"])
            fetch_cur_xp = fetch_data["contributed"]
            fetch_tot_pt = total_activity[stored_uuid] if stored_uuid in total_activity else 0
            fetch_week_pt = weekly_activity[stored_uuid] if stored_uuid in weekly_activity else 0
            fetch_lst_lgn = last_login[stored_uuid]

            member_info = requests.get(get_playerdb(stored_uuid)).json()
            if member_info['code'] != PLAYERDB_ERROR:
                fetch_uname = member_info['data']['player']['username']

            update_data = {
                "data":update_member_data(fetch_uname, fetch_ing_rank, fetch_cur_xp, fetch_lst_lgn, fetch_tot_pt, fetch_week_pt, current_row)
            }
            url_append = {"valueInputOption":"RAW"}

            update_sheet = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_UPDATE), update_data, "POST", url_append)

            if update_sheet and "error" in update_sheet:
                print("error occurred for posting request - edit member")
                print(update_sheet)
                pass #error logging
        else:
            update_data = {
                "data":old_member_data(current_row)
            }
            url_append = {"valueInputOption":"RAW"}

            update_sheet = attempt_google_api_interact(get_spreadsheet(MEMBER_SHEET_ID, SHEETS_UPDATE), update_data, "POST", url_append)

            if update_sheet and "error" in update_sheet:
                print("error occurred for posting request - old member")
                print(update_sheet)
                pass #error logging

# ACTIVATE SHEET MANAGEMENT FUNCTIONS

@loop(minutes=1)
async def loadmemberappend():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), MemberAppend)
    except:
        pass

@loop(minutes=30)
async def loadmemberupdate():
    try:
        await asyncio.get_event_loop().run_in_executor(ThreadPoolExecutor(), MemberUpdate)
    except:
        pass

#MAIN BOT FUNCTIONS CLASS

class SheetManager(commands.Cog):

    @commands.command()
    async def assign(self, ctx, discord, uuid):

        pass


# BOT COG SETUP

def setup(bot):
    bot.add_cog(SheetManager(bot))

#BOT LOOPING FUNCTIONS

loadmemberappend.start()
loadmemberupdate.start()
