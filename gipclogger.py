import requests
from datetime import datetime as dt
from copy import deepcopy
import json, time
import pytz
from pathlib import Path
import IDsnames as namesID
import re
import planetNames as planetNames
import regionNames as planetRegionData

baseDiretory = Path(__file__).resolve().parent # Me: Pega o diretório do programa
apiDataPath = baseDiretory / "apiData.json" # Me: pega o diretório do arquivo especificado

discordWebhook = None

imgURL = "https://i.imgur.com/8uwjWSZ.jpg"
dssGif = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNTh1eTd5dnh5eXY0NDhxb2FnM2VzeHc1Ync0ZHZlcW9pZ2g2aGg5ciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/puQc8qpqgAXda5lJPm/giphy.gif"
newsGif = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNjJ3dXkyNW55YmtpNmhxc2lpYnl1dWR1ejVwcjFkY2hibXRrejZraiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/yMwka6flHN3BEqrDxL/giphy.gif"
urlStatus = "https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/Status" 
urlWarinfo = "https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/WarInfo" 
urlDiveHarder = "https://api.diveharder.com/raw/all" 

startTimeConstant = 1706040313

apiStuff = {
    "planetData": [],
    "planetEvents": [],
    "planetActiveEffects": [],
    "regionData": [],
    "planetAttacks": [],
    "campaignData": [],
    "spaceStations": [],
    "newsFeed": [],
    "majorOrders": [],
    "generalInfo": {
        "startDate": None,
        "time": None,
        "impactMultiplier": None,
        "layoutVersion": None,
        "storyBeatId32": None,
    }
}

factionNames = {
    0: "Any",
    1: "Helldiver",
	2: "Terminid",
	3: "Automaton",
	4: "Illuminate"
}

gifsOwner = {
    1: "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzc0ZG51OHJpNGNqMmxydWEzbWx5NTdpODg4cnZzOHpoa2htNGMzaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5Yyp4ZWTuIjCm91mqK/giphy.gif",
    2: "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2lsemlzcTA5aTNweXd2YmtuZ2VsaHg3Z2hsa2lidWxkZ2k2Zmp6NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/gILlaUsbyaSU4wuM0F/giphy.gif",
    3: "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3FsNG4yNWVvZ3Y4NDNsanloaWY2ZW1tNGFlZW4wb2EwOWw2czJ6byZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/UirTbp2EQqyNRCV4w6/giphy.gif",
    4: "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGQ4bDdwZGEwNW5iZ291N3c0cDQ5YmJjN3cwMGw2ZHNkYm01anVsMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/OE6uoRAjq9OsW3Piii/giphy.gif"
}

eventTypes = {
        1: "Defense",
        2: "Invasion (guerilla)",
        3: "Invasion"
    }

campaignTypes = {
    0 : "Liberation",
    1 : "Recon",
    2 : "High Priority Campaign",
    3 : "Attrition",
    4 : "Event"
}

def createEmbed(title, description, image, timestamp):
    timestampNow = dt.now(pytz.timezone("UTC")).strftime("%Y/%m/%d, %H:%M:%S")
    
    embed = {
                "title": title,
                "color": 15158332,  # Red
                "timestamp": timestamp,
                "footer": {"text": "GENERAL PURPOSE INFORMATION LOGGER"},
            }
        
    if description:
        embed["description"] = description
    if image:
        embed["image"] = {"url": image}

        try:
            data = {"embeds": [embed]}
            response = requests.post(discordWebhook, json=data)
            time.sleep(1)
            if response.status_code != 204:
                print(f"Webhook falhou ({response.status_code}): {response.text}")
                time.sleep(2)
            print(f"[{timestampNow}] EMBED CREATED")
            embed = None
        except Exception as e:
            print(f"Falha ao enviar notificação Discord: {e}")
            time.sleep(2)

def saveAPIData():
    apiDataPath.write_text(json.dumps(apiStuff, indent=2, ensure_ascii=False), encoding='utf-8')
               
def loadAPIData():
    if apiDataPath.exists():
        return json.loads(apiDataPath.read_text(encoding='utf-8'))

def getPlanetName(planetIndex):
    try:
        for planet in apiStuff['planetData']:
            if planet['index'] == planetIndex: return planet.get('name')
    except:
        return None

def getRegionName(regionHash):
    try:
        for region in apiStuff['regionData']:
            if region['settingsHash'] == regionHash: return region.get('name')
    except:
        return None
    
def getRegionSize(regionHash):
    try:
        for region in apiStuff['regionData']:
            if region['settingsHash'] == regionHash: 
                size = region.get('regionSize')
                if size == 0: return ("SETTLEMENT")
                elif size == 1: return ("TOWN")
                elif size == 2: return ("CITY")
                elif size == 3: return ("MEGA CITY")
    except:
        return None

def sendNotificationRegion(planetIndex, filteredAttr, hash):

    gifURL = None
    filteredLines = []
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    
    planetName = getPlanetName(int(planetIndex))
    regionName = getRegionName(hash)
    regionSize = getRegionSize(hash)

    if not isinstance(planetName, str): return ("ERROR, NAME NOT FOUND")
    if not isinstance(regionName, str): return ("ERROR, NAME NOT FOUND")

    title = "🚨REGION UPDATE DETECTED!"
    filteredLines.append(f"**\nPLANET NAME: {planetName}**\n")
    filteredLines.append(f"**REGION NAME: {regionName}**\n")
    filteredLines.append(f"**REGION TYPE: {regionSize}**\n")

    for attr, difference in filteredAttr.items():

        if attr == 'owner':
            oldName = factionNames.get(difference['old'])
            newName = factionNames.get(difference['new'])
            gifURL = gifsOwner.get(difference['new'])

            if oldName == None: 
                title = "🚨NEW REGION DETECTED!"
                filteredLines.append(f"**{attr.upper()}:  {newName.upper()}**\n")
            else: 
                if difference["old"] == 1:
                    filteredLines.append(f"**{regionName.upper()} HAS FALLEN TO THE {newName.upper()}**\n")

                elif difference["new"] == 1:

                    filteredLines.append(f"**{regionName.upper()} HAS BEEN LIBERATED BY THE HELLDIVERS**\n")
                else:
                    filteredLines.append(f"**{attr.upper()}:  {oldName.upper()}  ➜  {newName.upper()}**\n")

        elif attr == 'regerPerSecond':
            oldRegen = difference['old']
            newRegen = difference['new']
            for region in apiStuff.get("regionData"):
                if region['settingsHash'] == hash:
                    maxHP = region['maxHealth']
            
            if oldRegen == None:
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP}HP:  %{(decayNew):.3f}/h**\n")

            else:
                decayOld = ((oldRegen*3600) / maxHP) * 100
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP}HP:  %{(decayOld):.3f}/h  ➜  %{(decayNew):.3f}/h**\n")

        elif attr == 'availabilityFactor':
            oldFactor = difference['old']
            newFactor = difference['new']

            if oldFactor == None:
                filteredLines.append(f"**AVAILABLE AT:  %{((1-newFactor)*100):.3f}**\n")

            else:
                filteredLines.append(f"**AVAILABLE AT:  %{((1-oldFactor)*100):.3f}  ➜  %{((1-newFactor)*100):.3f}**\n")

        elif attr == 'isAvailable':
            oldAvailable = difference['old']
            newAvailable = difference['new']

            if oldAvailable == None:
                filteredLines.append(f"**AVAILABLE:  {newAvailable}**\n")

            else:
                filteredLines.append(f"**AVAILABLE:  {oldAvailable} ➜ {newAvailable}**\n")
                
    filteredText = "\n".join(filteredLines)

    if gifURL:createEmbed(title, filteredText, gifURL, timestamp)
    else: createEmbed(title, filteredText, imgURL, timestamp)

def sendNotificationPlanet(planetIndex, filteredAttr):
    
    gifURL = None
    filteredLines = []
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()
    planetName = getPlanetName(int(planetIndex))
    if not isinstance(planetName, str): return ("ERROR, NAME NOT FOUND")

    filteredLines.append(f"**\nPLANET NAME: {planetName}**\n")

    for attr, difference in filteredAttr.items():

        if attr == 'owner':
            oldName = factionNames.get(difference['old'])
            newName = factionNames.get(difference['new'])
            gifURL = gifsOwner.get(difference['new'])

            if oldName == None: 
                title = "🚨NEW PLANET DETECTED!"
                filteredLines.append(f"**{attr.upper()}:  {newName.upper()}**\n")
            else: 
                if difference["old"] == 1:
                    filteredLines.append(f"**{planetName.upper()} HAS FALLEN TO THE {newName.upper()}**\n")

                elif difference["new"] == 1:
                    filteredLines.append(f"**{planetName.upper()} HAS BEEN LIBERATED BY THE HELLDIVERS**\n")

                else:
                    filteredLines.append(f"**{attr.upper()}:  {oldName.upper()}  ➜  {newName.upper()}**\n")

        elif attr == 'regenPerSecond':
            oldRegen = difference['old']
            newRegen = difference['new']

            for planet in apiStuff.get("planetData"):
                if planet['index'] == planetIndex:
                    maxHP = planet['maxHealth']
                    break
            
            if oldRegen == None:
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP}HP:  %{(decayNew):.3f}/h**\n")

            else:
                decayOld = ((oldRegen*3600) / maxHP) * 100
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP}HP:  %{(decayOld):.3f}/h ➜ %{(decayNew):.3f}/h**\n")
        
        elif attr == 'waypoints':
            oldWaypoints = difference['old'] or []
            newWaypoints = difference['new'] or []

            for planetIDNew in newWaypoints:
                if planetIDNew not in oldWaypoints:
                    planetNameWarpNew = getPlanetName(int(planetIDNew))
                    filteredLines.append(f"**WARP LINK ADDED FROM {planetName} TO {planetNameWarpNew}**\n")

            for planetIDOld in oldWaypoints:
                if planetIDOld not in newWaypoints:
                    planetNameWarpOld = getPlanetName(int(planetIDOld))
                    filteredLines.append(f"**WARP LINK REMOVED FROM {planetName} TO {planetNameWarpOld}**\n")
        
        elif attr == 'galacticEffectId':
            oldEffects = difference['old'] or []
            newEffects = difference['new'] or []

            for effectIDNew in newEffects:
                if effectIDNew not in oldEffects:

                    if effectIDNew in namesID.planetEffects:
                        effectNameNew = namesID.planetEffects[effectIDNew]
                        filteredLines.append(f"**EFFECT {effectNameNew.upper()} ({effectIDNew}) ADDED**\n")

                    else: filteredLines.append(f"**EFFECT {effectIDNew} ADDED**\n")

            for effectIDOld in oldEffects:
                if effectIDOld not in newEffects:
                    if effectIDOld in namesID.planetEffects:
                        effectNameOld = namesID.planetEffects[effectIDOld]
                        filteredLines.append(f"**EFFECT {effectNameOld.upper()} ({effectIDOld}) REMOVED**\n")

                    else: filteredLines.append(f"**EFFECT {effectIDOld} REMOVED**\n")

        else: filteredLines.append(f"**{attr.upper()}: {difference['old']} ➜ {difference['new']}**\n")

    title = "🚨PLANET UPDATE DETECTED!"
    filteredText = "\n".join(filteredLines)

    if gifURL:createEmbed(title, filteredText, gifURL, timestamp)
    else: createEmbed(title, filteredText, imgURL, timestamp)

def sendNotificationEvent(hasEnded, event, deviation):

    gifURL = None
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if not hasEnded:

        expiresAt = event.get("expireTime")
        startedAt = event.get("startTime")
        type = event.get("eventType")
        race = event.get("race")
        pIndex = event.get("planetIndex")
        defenseLevel = int(event.get("maxHealth")) / 50000

        typeEvent = eventTypes.get(type)
        faction = factionNames.get(race)

        startedAtAtReal = startTimeConstant + startedAt + deviation
        expiresAtReal = startTimeConstant + expiresAt + deviation

        planetAttacks = apiStuff.get("planetAttacks", [])
        attackList = []

        if pIndex in planetNames.planet_names: pName = planetNames.planet_names.get(pIndex)
        if not isinstance(faction, str): return ("ERROR, NAME NOT FOUND")
        if not isinstance(typeEvent, str): return ("ERROR, NAME NOT FOUND")
        gifURL = gifsOwner.get(race)
        
        for planet in planetAttacks:
            sourceID = planet.get("source")
            targetID = planet.get("target")
            if pIndex == targetID:
                if sourceID in planetNames.planet_names: 
                    pNameSource = planetNames.planet_names.get(sourceID)
                    attackList.append(pNameSource)
                    attackText = " ".join(attackList)
                break

        title = "🚨PLANET EVENT STARTED!"
        descriptionList = []
        descriptionList.append(f"**\nPLANET NAME: {pName}**\n")
        descriptionList.append(f"**EVENT TYPE: {typeEvent.upper()}**\n")
        descriptionList.append(f"**PLANET ATTACKED BY THE: {faction.upper()}**\n")
        descriptionList.append(f"**ATTACK SOURCE(S): {attackText}**\n")
        descriptionList.append(f"**{typeEvent.upper()} LEVEL: {int(defenseLevel)}**\n")
        descriptionList.append(f"**{typeEvent.upper()} TOTAL HP: {int(defenseLevel)*50000}**\n")
        descriptionList.append(f"**{typeEvent.upper()} STARTED**: <t:{startedAtAtReal}>\n")
        descriptionList.append(f"**{typeEvent.upper()} ENDS**: <t:{expiresAtReal}>\n")

        descriptionText = "\n".join(descriptionList)
        createEmbed(title, descriptionText, gifURL, timestamp)


    if hasEnded:
        race = event.get("race")
        pIndex = event.get("planetIndex")
        type = event.get("eventType")
        typeEvent = eventTypes.get(type)
        faction = factionNames.get(race)
        currentPlanetData = deepcopy(apiStuff["planetData"])
        hasLost = True

        for currentPlanet in currentPlanetData:
            if pIndex == currentPlanet['index']:
                currentOwner = currentPlanet['owner']
                if race != currentOwner: hasLost = False
                break
     
        if pIndex in planetNames.planet_names: pName = planetNames.planet_names.get(pIndex)
        if not isinstance(faction, str): faction = ("name not found")
        if not isinstance(typeEvent, str): typeEvent = ("name not found")

        title = "🚨PLANET EVENT ENDED!"
        descriptionList = [] 
        descriptionList.append(f"**\nPLANET NAME: {pName}**\n")
        descriptionList.append(f"**EVENT TYPE: {typeEvent.upper()}**\n")
        descriptionList.append(f"**PLANET ATTACKED BY THE: {faction.upper()}**\n")
        
        if hasLost:
            gifURL = gifsOwner.get(race)
            descriptionList.append(f"**THE HELLDIVERS HAVE LOST THE {typeEvent.upper()} TO {faction.upper()}\n**")

        if not hasLost:
            gifURL = gifsOwner.get(currentOwner)
            descriptionList.append(f"**THE HELLDIVERS HAVE WON THE {typeEvent.upper()} AGAINST THE {faction.upper()}\n**")

        descriptionText = "\n".join(descriptionList)
        createEmbed(title, descriptionText, gifURL, timestamp)

def sendNotificationDSS(newPIndex, oldPIndex, newEffects, oldEffects):

    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if oldPIndex in planetNames.planet_names: oldName = planetNames.planet_names.get(oldPIndex)
    else: return ("ERROR, NO NAME")

    if newPIndex in planetNames.planet_names: newName = planetNames.planet_names.get(newPIndex)
    else: return ("ERROR, NO NAME")

    if not newPIndex == oldPIndex:
        textList = []
        textList.append(f"**\nDSS HAS WARPED FROM {oldName.upper()} ➜ {newName.upper()}**\n")
    
    if not newEffects == oldEffects:
        
        for effectIDNew in newEffects:
            if effectIDNew not in oldEffects:
                textList = []
                if effectIDNew in namesID.planetEffects:
                    effectNameNew = namesID.planetEffects[effectIDNew]
                    textList.append(f"**EFFECT {effectNameNew.upper()} ({effectIDNew}) ADDED**\n")

                else:textList.append(f"**EFFECT {effectIDNew} ADDED**\n")
                
        for effectIDOld in oldEffects:
            if effectIDOld not in newEffects:
                textList = []
                if effectIDOld in namesID.planetEffects:
                    effectNameOld = namesID.planetEffects[effectIDOld]
                    textList.append(f"**EFFECT {effectNameOld.upper()} ({effectIDOld}) ENDED**\n")

                else:textList.append(f"**EFFECT {effectIDOld} ENDED**\n")
                
    title = "🚨DSS UPDATE!"
    textDescription = "".join(textList)
    createEmbed(title, textDescription, dssGif, timestamp)

def sendNotificationGenInfo(oldData):
    oldGenInfo = deepcopy(oldData.get('generalInfo', []))
    newGenInfo = deepcopy(apiStuff.get('generalInfo', []))
    
    if newGenInfo == oldGenInfo: return
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if not oldGenInfo:
        newLayout = newGenInfo["layoutVersion"]
        newStoryID = newGenInfo["storyBeatId32"]

        descriptionLines = []
        title = "🚨GENERAL INFO UPDATED!"
        descriptionLines.append(f"**LAYOUT VERSION: {newLayout}**")
        descriptionLines.append(f"**STORY BEAT ID: {newStoryID}**")

        description = "\n".join(descriptionLines)
        createEmbed(title, description, imgURL, timestamp)

    else:
        oldLayout = oldGenInfo["layoutVersion"]
        oldStoryID = oldGenInfo["storyBeatId32"]
        newLayout = newGenInfo["layoutVersion"]
        newStoryID = newGenInfo["storyBeatId32"]

        descriptionLines = []
        title = "🚨GENERAL INFO UPDATED!"
        if oldLayout != newLayout: descriptionLines.append(f"**LAYOUT VERSION: {oldLayout} ➜ {newLayout}**")
        if oldStoryID != newStoryID: descriptionLines.append(f"**STORY BEAT ID: {oldStoryID} ➜ {newStoryID}**")
        if not descriptionLines: return

        description = "\n".join(descriptionLines)
        createEmbed(title, description, imgURL, timestamp)

def sendNotificationCampaign(oldData):
    oldCampaign = deepcopy(oldData.get("campaignData", []))
    newCampaign = deepcopy(apiStuff.get("campaignData", []))
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if oldCampaign == newCampaign: return

    oldDict = {campaign["id"]: campaign for campaign in oldCampaign}
    newDict = {campaign["id"]: campaign for campaign in newCampaign}

    oldIDs = set(oldDict.keys())
    newIDs = set(newDict.keys())

    hasEndedIDs = oldIDs - newIDs
    hasStartedIDs = newIDs - oldIDs
    equalIDs = oldIDs & newIDs
    title = "🚨CAMPAIGN UPDATED!"

    for campaignId in hasEndedIDs:
        descriptionLines = []
        campaign = oldDict[campaignId]
        pIndexOld = campaign.get("planetIndex")
        pCampaignTypeOld = campaign.get("type")
        pCampaignNameOld = campaignTypes.get(pCampaignTypeOld)
        pNameOld = getPlanetName(int(pIndexOld))
        descriptionLines.append(f"**{pCampaignNameOld.upper()} CAMPAIGN ON {pNameOld.upper()} HAS ENDED**\n")

        descriptionText = "\n".join(descriptionLines)
        createEmbed(title, descriptionText, imgURL, timestamp)

    for campaignId in hasStartedIDs:
        descriptionLines = []
        campaign = newDict[campaignId]
        pIndexNew = campaign.get("planetIndex")
        pCampaignTypeNew = campaign.get("type")
        pCampaignNameNew = campaignTypes.get(pCampaignTypeNew)
        pNameNew = getPlanetName(int(pIndexNew))
        descriptionLines.append(f"**{pCampaignNameNew.upper()} CAMPAIGN ON {pNameNew.upper()} HAS STARTED**\n")
        
        descriptionText = "\n".join(descriptionLines)
        createEmbed(title, descriptionText, imgURL, timestamp)

    for campaignId in equalIDs:
        descriptionLines = []
        oldCamp = oldDict[campaignId]
        newCamp = newDict[campaignId]
        pName = getPlanetName(int(newCamp["planetIndex"]))

        if oldCamp["type"] != newCamp["type"]:
            oldType = campaignTypes[oldCamp["type"]] 
            newType = campaignTypes[newCamp["type"]] 
            descriptionLines.append(f"**CAMPAIGN ON {pName.upper()} CHANGED FROM {oldType.upper()}  ➜  {newType.upper()}**\n")

            descriptionText = "\n".join(descriptionLines)
            createEmbed(title, descriptionText, imgURL, timestamp)

def sendNotificationGlobalEvent(oldData):
    oldGlobal = deepcopy(oldData.get("globalEvents", []))
    newGlobal = deepcopy(apiStuff.get("globalEvents", []))
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    newGlobalDict = {globalEvent["eventId"]: globalEvent for globalEvent in newGlobal}
    oldGlobalDict = {globalEvent["eventId"]: globalEvent for globalEvent in oldGlobal}

    if newGlobalDict == oldGlobalDict: return

    oldIDs = set(oldGlobalDict.keys())
    newIDs = set(newGlobalDict.keys())

    hasEndedIDs = oldIDs - newIDs
    hasStartedIDs = newIDs - oldIDs

    for globalEventID in hasEndedIDs:
        descriptionLines = []
        globalEventEnded = oldGlobalDict[globalEventID]

        title = (f"🚨GLOBAL EVENT ENDED")
        titleEvent = globalEventEnded.get("title")
        message = globalEventEnded.get("message")
        cleanedMessage = re.sub("<i=1>|</i>", "", message)
        effectGlobal = globalEventEnded.get("effectIds")

        if titleEvent != "": descriptionLines.append(f"**{titleEvent}**\n")
        else: descriptionLines.append(f"**NO TITLE**\n")

        if cleanedMessage != "": descriptionLines.append(f"**{cleanedMessage}**")
        else: descriptionLines.append(f"**NO MESSAGE**")
        
        if effectGlobal:
            for effect in effectGlobal:
                if effect in namesID.planetEffects:
                    effectName = namesID.planetEffects[effect]
                    descriptionLines.append(f"**EFFECT ENDED {effectName} ({effect})\n**")

                else:descriptionLines.append(f"**EFFECT ENDED {effect}\n**")
        
        descriptionText = "\n".join(descriptionLines)

        createEmbed(title, descriptionText, imgURL, timestamp)
        
    for globalEventID in hasStartedIDs:
        descriptionLines = []
        globalEventStarted = newGlobalDict[globalEventID]

        title = (f"🚨GLOBAL EVENT STARTED")
        message = globalEventStarted.get("message")
        cleanedMessage = re.sub("<i=1>|</i>", "", message)
        titleEvent = globalEventStarted.get("title")
        effectGlobal = globalEventStarted.get("effectIds")

        if titleEvent != "": descriptionLines.append(f"**{titleEvent}**\n")
        else: descriptionLines.append(f"**NO TITLE**\n")

        if cleanedMessage != "": descriptionLines.append(f"**{cleanedMessage}**")
        else: descriptionLines.append(f"**NO MESSAGE**")
        
        if effectGlobal:
            for effect in effectGlobal:
                if effect in namesID.planetEffects:
                    effectName = namesID.planetEffects[effect]
                    descriptionLines.append(f"**EFFECT ADDED {effectName} ({effect})\n**")

                else:descriptionLines.append(f"**EFFECT ADDED {effect}\n**")

        gametime = apiStuff["generalInfo"].get("time")
        expiresAt = globalEventStarted.get("expireTime")

        unixNow = int(dt.now().timestamp())
        deviation =  unixNow - (startTimeConstant + gametime)
        expiresAtReal = startTimeConstant + expiresAt + deviation

        descriptionLines.append(f"**\nGLOBAL EVENT ENDS**: <t:{expiresAtReal}>\n")
        descriptionText = "\n".join(descriptionLines)

        createEmbed(title, descriptionText, imgURL, timestamp)

def sendNotificationNews(oldData):

    oldNews = deepcopy(oldData.get('newsFeed', []))
    newNews = deepcopy(apiStuff.get('newsFeed', []))
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if newNews == oldNews: return

    oldDict = {news["id"]: news for news in oldNews}
    newDict = {news["id"]: news for news in newNews}

    oldIDs = set(oldDict.keys())
    newIDs = set(newDict.keys())

    hasStartedIDs = newIDs - oldIDs

    for newsID in hasStartedIDs:
        news = newDict[newsID]
        descriptionLines = []
        gametime = apiStuff["generalInfo"].get("time")
        publishedAt = news.get("published")
        message = news.get("message")
        cleanedMessage = re.sub("<i=1>|</i>|<i=3>", "", message)

        unixNow = int(dt.now().timestamp())
        deviation =  unixNow - (startTimeConstant + gametime)
        publishedAtReal = startTimeConstant + publishedAt + deviation

        title = (f"🚨SUPER EARTH NEWS!")
        descriptionLines.append(f"**{cleanedMessage}**\n")
        descriptionLines.append(f"**SUPER NEWS PUBLISHED AT** <t:{publishedAtReal}>\n")
        descriptionText = "\n".join(descriptionLines)

        createEmbed(title, descriptionText, newsGif, timestamp)

def sendNotificationMajorOrder(oldData):

    oldMajorOrder = deepcopy(oldData.get('majorOrders', []))
    newMajorOrder = deepcopy(apiStuff.get('majorOrders', []))

    oldDict = {majorOrders["id32"]: majorOrders for majorOrders in oldMajorOrder}
    newDict = {majorOrders["id32"]: majorOrders for majorOrders in newMajorOrder}

    oldIDs = set(oldDict.keys())
    newIDs = set(newDict.keys())

    if newIDs == oldIDs: return

    itemsIDs = deepcopy(namesID.itemID)
    
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    hasStartedIDs = newIDs - oldIDs
    unixNow = int(dt.now().timestamp())
    gametime = apiStuff["generalInfo"].get("time")
    
    for majorOrderID in hasStartedIDs:
        majorOrder = newDict[majorOrderID]

        expiresAt = majorOrder.get("expiresIn")
        startedAt = majorOrder.get("startTime")
        
        deviation =  unixNow - (startTimeConstant + gametime)
        startedAtAtReal = startTimeConstant + startedAt + deviation
        expiresAtReal = startTimeConstant + (expiresAt + startedAt) + deviation
        fromNow = dt.fromtimestamp(unixNow)
        fromLater = dt.fromtimestamp(expiresAtReal)
        timeTillEnd = fromLater - fromNow
        totalHours = timeTillEnd.total_seconds() / 3600

        days = totalHours / 24
        hours = (days - int(days))* 24
        minutes = (hours - int(hours)) * 60
        
        settingsList = majorOrder.get("setting")
        majorOrderBriefing = settingsList.get("overrideBrief")
        tasksList = settingsList.get("tasks")
        titleOrder = settingsList.get("overrideTitle")
        if titleOrder: 
            title = (f"🚨{titleOrder}")
            
        else: title = (f"🚨MAJOR/SIDE ORDER")
        
        descriptionList = []
        descriptionList.append(f"\n**DISPATCH: {majorOrderBriefing}**\n")

        for tasks in tasksList:
            
            if tasks["type"] == 2:
                # Gather
                for tam in range(len(tasks["valueTypes"])):

                    if tasks["valueTypes"][tam] == 1:
                        factionID = tasks["values"][tam]
                        if factionID == None: break
                        factionName = factionNames.get(factionID)
                    
                    elif tasks["valueTypes"][tam] == 3:
                        goal = tasks["values"][tam]
                        if goal == None: break

                    elif tasks["valueTypes"][tam] == 5:
                        itemID = tasks["values"][tam]
                        if itemID == None: break
                        if itemID in itemsIDs:
                            itemName = itemsIDs.get(itemID)
                        else: itemName = "UNKNOWN"

                descriptionList.append(f"**GATHER {goal} {itemName.upper()} FROM {factionName.upper()} PLANETS**\n")

            elif tasks["type"] == 3:
                #Eradicate
                for tam in range(len(tasks["valueTypes"])):
                    
                    if tasks["valueTypes"][tam] == 3:
                        goal = tasks["values"][tam]
                        if goal == None: break

                    elif tasks["valueTypes"][tam] == 5:
                        itemID = tasks["values"][tam]
                        if itemID == None: break
                        if itemID in itemsIDs:
                            itemName = itemsIDs.get(itemID)
                        else: itemName = "UNKNOWN"
                        
                descriptionList.append(f"**KILL {goal} {itemName.upper()}**\n")

            elif tasks["type"] == 4:
                #Objectives ??
                print(tasks["type"])

            elif tasks["type"] == 7:
                #Extract
                print(tasks["type"])

            elif tasks["type"] == 9:
                #Operations
                print(tasks["type"])

            elif tasks["type"] == 11:
                #Liberation
                for tam in range(len(tasks["valueTypes"])):
                    if tasks["valueTypes"][tam] == 12:
                        planetID = tasks["values"][tam]
                        if planetID == None: break
                        planetName = getPlanetName(planetID)
                
                descriptionList.append(f"**LIBERATE THE PLANET {planetName}**\n")

            elif tasks["type"] == 12:
                #Defense
                for tam in range(len(tasks["valueTypes"])):

                    if tasks["valueTypes"][tam] == 1:
                        factionID = tasks["values"][tam]
                        if factionID == None: break
                        factionName = factionNames.get(factionID)
                    
                    elif tasks["valueTypes"][tam] == 3:
                        goal = tasks["values"][tam]
                        if goal == None: break
                
                descriptionList.append(f"**DEFEND AGAINST {goal} FROM THE {factionName.upper()}**\n")

            elif tasks["type"] == 13:
                # Control = Hold
                for tam in range(len(tasks["valueTypes"])):
                    if tasks["valueTypes"][tam] == 12:
                        planetID = tasks["values"][tam]
                        if planetID == None: break
                        planetName = getPlanetName(planetID)
                
                descriptionList.append(f"**HOLD THE PLANET {planetName}**\n")

            elif tasks["type"] == 15:
                #Conquest
                print(tasks["type"])

        descriptionList.append(f"**ORDER BEGUN <t:{startedAtAtReal}>**\n")
        descriptionList.append(f"**ORDER ENDS IN {round(days)} DAYS, {round(hours)} HOURS AND {round(minutes)} MINUTES**\n")
        descriptionText = "\n".join(descriptionList)
        createEmbed(title, descriptionText, imgURL, timestamp)

def updateRegionData(oldData):

    oldRegions = deepcopy(oldData.get("regionData", []))
    newRegions = deepcopy(apiStuff.get("regionData", []))

    if oldRegions == newRegions: return
    
    oldRegionMap = {f"{region['planetIndex']}_{region['regionIndex']}": region for region in oldRegions}
    newRegionMap = {f"{region['planetIndex']}_{region['regionIndex']}": region for region in newRegions}

    regionChanges = {}
    update = False
    timestamp = dt.now(pytz.timezone("UTC")).strftime("%Y/%m/%d, %H:%M:%S")

    for keyStr, newRegion in newRegionMap.items():
        oldRegion = oldRegionMap.get(keyStr)

        for attr, newValue in newRegion.items():
            oldValue = oldRegion.get(attr)

            if oldValue != newValue:
                if keyStr not in regionChanges:
                    regionChanges[keyStr] = {'changes': []}

                regionChanges[keyStr]['changes'].append({
                    'attribute': attr,
                    'old': oldValue,
                    'new': newValue
                })
                oldRegion[attr] = newValue
                update = True

        if keyStr in regionChanges:
            changeList = regionChanges[keyStr]['changes']
            changeDict = {item['attribute']: {'old': item['old'], 'new':item['new']} for item in changeList}

            filterAttr = {'owner', 'regerPerSecond', 'isAvailable', 'availabilityFactor'}
            filteredAttr = {aFilter: valueFilter for aFilter, valueFilter in changeDict.items() if aFilter in filterAttr}
            pIndex, _ = keyStr.split("_")
            
            if filteredAttr :
                    sendNotificationRegion(pIndex, filteredAttr, hash = oldRegion['settingsHash'])
        
    apiStuff["regionData"] = list(oldRegionMap.values())

    if update:
        regionHealthChanges = {}
        for regionID, changeData in regionChanges.items():
            filterHealth = []
            
            for change in changeData["changes"]:
                if change["attribute"] == "health":
                    filterHealth.append(change)

            if filterHealth:
                regionHealthChanges[regionID] = filterHealth

        if regionHealthChanges:
            with open('regionHealthChange.json', 'w', encoding='utf-8') as file:
                json.dump(regionHealthChanges, file, indent=2, ensure_ascii=False)
                file.write("\n") 
            print(f"[{timestamp}] {len(regionHealthChanges)} REGIONS HAD HEALTH CHANGES.")
        else:
            print(f"[{timestamp}] NO REGION HEALTH CHANGE")

    else: print(f"[{timestamp}] NO REGION UPDATE")

def updatePlanetData(oldData):
    oldPlanets = deepcopy(oldData.get('planetData',[]))
    newPlanets = deepcopy(apiStuff.get('planetData',[]))

    if oldPlanets == newPlanets: return

    oldPlanetMap = {planet['index']: planet for planet in oldPlanets}
    newPlanetMap = {planet['index']: planet for planet in newPlanets}

    planetChanges = {}
    update = False
    timestamp = dt.now(pytz.timezone("UTC")).strftime("%Y/%m/%d, %H:%M:%S")

    for index, newPlanet in newPlanetMap.items():
        oldPlanet = oldPlanetMap.get(index)

        for attr, newValue in newPlanet.items():
            oldValue = oldPlanet.get(attr)

            if newValue != oldValue:

                if index not in planetChanges:
                    planetChanges[index] = {'changes': []}

                planetChanges[index]['changes'].append({
                    'attribute': attr,
                    'old': oldValue,
                    'new': newValue
                })

                oldPlanet[attr] = newValue
                update = True

        if index in planetChanges:
            changeList = planetChanges[index]['changes']
            changeDict = {item['attribute']: {'old': item['old'], 'new':item['new']} for item in changeList}

            filterAttr = {'owner', 'regenPerSecond', 'disabled', 'maxHealth', 'waypoints', 'galacticEffectId'}
            filteredAttr = {aFilter: valueFilter for aFilter, valueFilter in changeDict.items() if aFilter in filterAttr}

            if filteredAttr:
                sendNotificationPlanet(index, filteredAttr)
    
    apiStuff["planetData"] = list(oldPlanetMap.values())

    if update:
        planetHealthChanges = {}
        for planetID, changeData in planetChanges.items():
            filterHealth = []
            for change in changeData["changes"]:
                if change["attribute"] == "health":
                    filterHealth.append(change)
            if filterHealth:
                planetHealthChanges[planetID] = filterHealth

        if planetHealthChanges:
            with open('planetsHealthChange.json', 'w', encoding='utf-8') as file:
                json.dump(planetHealthChanges, file, indent=2, ensure_ascii=False)
                file.write("\n")             
            print(f"[{timestamp}] {len(planetHealthChanges)} PLANETS HAD HEALTH CHANGES.")
            
        else:
            print(f"[{timestamp}] NO PLANET HEALTH CHANGE")

    else: print(f"[{timestamp}] NO PLANET UPDATE")

def updatePlanetEvents(oldData):
    oldEvents = deepcopy(oldData.get('planetEvents',[]))
    newEvents = deepcopy(apiStuff.get('planetEvents',[]))

    if oldEvents == newEvents: return

    oldEventMap = {event['id']: event for event in oldEvents}
    newEventMap = {event['id']: event for event in newEvents}
    gametime = apiStuff["generalInfo"].get("time")
    unixNow = int(dt.now().timestamp())
    deviation =  unixNow - (startTimeConstant + gametime)

    healthChanges = {}

    for idNew, newEvent in newEventMap.items():
        if idNew not in oldEventMap:
            hasEnded = False
            sendNotificationEvent(hasEnded, newEvent, deviation)

        elif idNew in oldEventMap:
            oldEvent = oldEventMap[idNew]
            oldHP = oldEvent.get("health")
            newHP = newEvent.get("health")

            if newHP != oldHP:
                healthChanges[idNew] = {
                    "planetIndex": newEvent.get("planetIndex"),
                    "old": oldHP,
                    "new": newHP
                }
    
    timestamp = dt.now(pytz.timezone("UTC")).strftime("%Y/%m/%d, %H:%M:%S")

    if healthChanges:
            with open('eventsHealthChange.json', 'w', encoding='utf-8') as file:
                json.dump(healthChanges, file, indent=2, ensure_ascii=False)
                file.write("\n")  
            print(f"[{timestamp}] {len(healthChanges)} PLANET EVENTS HAD HEALTH CHANGES.")

    else:
        print(f"[{timestamp}] NO PLANET EVENT HEALTH CHANGE")           
    
    for idOld, oldEvent in oldEventMap.items():
        if idOld not in newEventMap:
            hasEnded = True
            sendNotificationEvent(hasEnded, oldEvent, deviation)

def updateDSS(oldData):
    oldDSS = deepcopy(oldData.get('spaceStations', []))
    newDSS = deepcopy(apiStuff.get('spaceStations', []))
    
    if newDSS == oldDSS: return

    newPIndex = newDSS[0]['planetIndex']; oldPIndex = oldDSS[0]['planetIndex']
    newEffects = newDSS[0]['activeEffectIds']; oldEffects = oldDSS[0]['activeEffectIds']
    newElection = newDSS[0]['currentElectionEndWarTime']; oldElection = oldDSS[0]['currentElectionEndWarTime']
    changedPIndex = newPIndex != oldPIndex
    changedEffects = newEffects != oldEffects
    changedElection = newElection != oldElection

    if changedElection and not (changedPIndex or changedEffects): return
    sendNotificationDSS(newPIndex, oldPIndex, newEffects, oldEffects)
   
def getAPIInfo():

    staticRequest = requests.get(urlWarinfo) 
    if staticRequest.status_code == 200:
        staticData = staticRequest.json() 
    else:
        print(f"Failed to retrieve API data {staticRequest.status_code}.")
        time.sleep(4)
        return 
    
    statusRequest = requests.get(urlStatus) 
    if statusRequest.status_code == 200:
        statusData = statusRequest.json() 
    else:
        print(f"Failed to retrieve API data {statusRequest.status_code}.")
        time.sleep(4)
        return 
    
    diveharderRequest = requests.get(urlDiveHarder) 
    if diveharderRequest.status_code == 200:
        diveHarder = diveharderRequest.json() 
    else:
        print(f"Failed to retrieve API data {diveharderRequest.status_code}.")
        time.sleep(4)
        return 
    
    diveharderRequest = None
    staticRequest = None
    statusRequest = None

    staticPlanet = [deepcopy(planetStatic) for planetStatic in staticData['planetInfos']] 
    statusPlanet = [deepcopy(planetStatus) for planetStatus in statusData['planetStatus']] 
    staticRegion = [deepcopy(regionStatic) for regionStatic in staticData['planetRegions']]
    statusRegion = [deepcopy(regionStatus) for regionStatus in statusData['planetRegions']]
    diveNewsFeed = [deepcopy(newsFeed) for newsFeed in diveHarder['news_feed']]
    
    staticMapPlanet = {planet['index']: planet for planet in staticPlanet} 
    statusMapPlanet = {planet['index']: planet for planet in statusPlanet} 

    for key, status in statusMapPlanet.items(): 
        if key in staticMapPlanet: 
            combinePlanets = deepcopy(staticMapPlanet[key]) 
            for attr, value in status.items(): 
                if attr == 'health':
                    if combinePlanets['maxHealth'] < value:
                        combinePlanets['maxHealth'] = value; combinePlanets['health'] = value

                    else: combinePlanets['health'] = value
                else:
                    if attr not in combinePlanets: 
                        combinePlanets[attr] = value 
                    else: 
                        if combinePlanets[attr] != value: combinePlanets[attr] = value
                
            staticMapPlanet[key] = combinePlanets 
    
    planetActiveEffects = statusData.get("planetActiveEffects", [])
    effectsGrouped = {}
    for effect in planetActiveEffects:
        effectPIndex = effect.get('index')
        effectID = effect.get('galacticEffectId')

        if effectPIndex not in effectsGrouped:
            effectsGrouped[effectPIndex] = []

        effectsGrouped[effectPIndex].append(effectID)
    
    for planetIndex, _ in staticMapPlanet.items(): 
        if planetIndex in planetNames.planet_names: staticMapPlanet[planetIndex]['name'] = planetNames.planet_names[planetIndex]
        staticMapPlanet[planetIndex]['galacticEffectId'] = effectsGrouped.get(planetIndex, [])
        
    staticMapRegion = {(region['planetIndex'], region['regionIndex']): region for region in staticRegion}
    statusMapRegion = {(region['planetIndex'], region['regionIndex']): region for region in statusRegion}

    for tupla, static in staticMapRegion.items():
        
        if tupla in statusMapRegion:
            combineRegions = deepcopy(statusMapRegion[tupla])
            for attr, value in static.items():
                if attr not in combineRegions: combineRegions[attr] = value
                else: 
                    if combineRegions[attr] != value: combineRegions[attr] = value
            staticMapRegion[tupla] = combineRegions
    
    for tupla, region in staticMapRegion.items(): 
        regionHash = region['settingsHash']
        if regionHash in planetRegionData.planetRegion: staticMapRegion[tupla]['name'] = planetRegionData.planetRegion[regionHash]
    
    lastestNews = diveNewsFeed[-10:]

    apiStuff["planetData"] = list(staticMapPlanet.values()) 
    apiStuff["planetEvents"] = statusData.get("planetEvents", [])
    apiStuff['planetActiveEffects'] = statusData.get("planetActiveEffects", [])
    apiStuff["regionData"] = list(staticMapRegion.values()) 
    apiStuff['planetAttacks'] = statusData.get("planetAttacks", [])
    apiStuff['campaignData'] = statusData.get("campaigns", [])
    apiStuff['spaceStations'] = statusData.get("spaceStations", [])
    apiStuff['globalEvents'] = statusData.get("globalEvents", [])
    apiStuff['newsFeed'] =  lastestNews
    apiStuff['majorOrders'] = diveHarder.get("major_order", [])
    apiStuff['generalInfo'] = {
        "startDate": staticData.get("startDate"),
        "time": statusData.get("time"),
        "impactMultiplier": statusData.get("impactMultiplier"),
        "layoutVersion": statusData.get("layoutVersion"),
        "storyBeatId32": statusData.get("storyBeatId32"),
    }

def main(discordWebhook):
    if discordWebhook == None:
        print("INSERT YOUR DISCORD WEBHOOK LINK. PLEASE MAKE SURE IT IS CORRECT, OTHERWISE YOU HAVE TO MANUALLY CORRECT IT.\n")
        webHookLink = input("WEBHOOK LINK: ")
        if isinstance(webHookLink, str): 
            print("\nLINKING SUCESSFUL")
            input("\nPress any key to continue")
            discordWebhook = webHookLink

        else: 
            print("\nLINKING IS WRONG, TRY MANUALLY INSERTING IT.")
            input("\nPress any key to continue")
            return 0

    getAPIInfo()

    if not apiDataPath.exists():
        print("Initializing API file")
        saveAPIData()

    while True:
        timestampStart = dt.now(pytz.timezone("UTC")).strftime("%Y/%m/%d, %H:%M:%S")
        print(f"[{timestampStart}]")
        time.sleep(30)
        getAPIInfo()
        oldData = loadAPIData()

        if oldData: 
            updatePlanetData(oldData)
            updateRegionData(oldData)
            updatePlanetEvents(oldData)
            updateDSS(oldData)
            sendNotificationMajorOrder(oldData)
            sendNotificationGlobalEvent(oldData)
            sendNotificationCampaign(oldData)
            sendNotificationNews(oldData)
            sendNotificationGenInfo(oldData)
            saveAPIData()
        
if __name__ == "__main__":
    main(discordWebhook)