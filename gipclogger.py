import requests
from datetime import datetime as dt
from copy import deepcopy
import json, time
import pytz
from pathlib import Path

with open("planetRegion.json", "r", encoding="utf-8") as file:
        planetRegionData = json.load(file)

with open("planet_names.json", "r", encoding="utf-8") as file:
    planet_names = json.load(file)

startTimeConstant = 1706040313

baseDiretory = Path(__file__).resolve().parent # Me: Pega o diretório do programa
apiDataPath = baseDiretory / "apiData.json" # Me: pega o diretório do arquivo especificado

imgURL = "https://i.imgur.com/8uwjWSZ.jpg"
dssGif = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExNTh1eTd5dnh5eXY0NDhxb2FnM2VzeHc1Ync0ZHZlcW9pZ2g2aGg5ciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/puQc8qpqgAXda5lJPm/giphy.gif"

discordWebhook = None
urlStatus = "https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/Status" # Status = Decay, total pop, updates in real time
urlWarinfo = "https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/WarInfo" # WarInfo = Static info, has region and planet index, max health

apiStuff = {
    "planetData": [],
    "planetEvents": [],
    "planetActiveEffects": [],
    "regionData": [],
    "planetAttacks": [],
    "campaignData": [],
    "spaceStations": [],
    "generalInfo": {
        "startDate": None,
        "time": None,
        "impactMultiplier": None,
        "layoutVersion": None,
        "storyBeatId32": None,
    }
}

factionNames = {
    "1": "Helldivers",
	"2": "Terminids",
	"3": "Automatons",
	"4": "Illuminates"
}

gifsOwner = {
    "1": "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzc0ZG51OHJpNGNqMmxydWEzbWx5NTdpODg4cnZzOHpoa2htNGMzaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5Yyp4ZWTuIjCm91mqK/giphy.gif",
    "2": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExN2lsemlzcTA5aTNweXd2YmtuZ2VsaHg3Z2hsa2lidWxkZ2k2Zmp6NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/gILlaUsbyaSU4wuM0F/giphy.gif",
    "3": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3FsNG4yNWVvZ3Y4NDNsanloaWY2ZW1tNGFlZW4wb2EwOWw2czJ6byZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/UirTbp2EQqyNRCV4w6/giphy.gif",
    "4": "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGQ4bDdwZGEwNW5iZ291N3c0cDQ5YmJjN3cwMGw2ZHNkYm01anVsMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/OE6uoRAjq9OsW3Piii/giphy.gif"
}

eventTypes = {
        "1": "Defense",
        "2": "Invasion (guerilla)",
        "3": "Invasion"
    }

campaignTypes = {
    "0" : "Liberation",
    "1" : "Recon",
    "2" : "High Priority Campaign",
    "3" : "Attrition",
    "4" : "Event"
}

actionsDSS = {
    "1209" : "Eagle Storm",
    "1210" : "Orbital Blockade",
    "1214" : "Heavy Ordinance Distribution"
}

lastNotifiedRegion = {}

lastNotifiedPlanet = {}

HTTP_PORT = 8080

ALLOWED_FILES = {
    "planetsHealthChange.json",
    "regionHealthChange.json",
    "apiData.json",
    "eventsHealthChange.json"
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
            if response.status_code != 204:
                print(f"Webhook falhou ({response.status_code}): {response.text}")
                time.sleep(2)
            print(f"[{timestampNow}] EMBED CREATED")
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
        planets = loadAPIData()
        for planet in planets['planetData']:
            if planet['index'] == planetIndex: return planet.get('name')
    except:
        return None

def getRegionName(regionHash):
    try:
        regions = loadAPIData()
        for region in regions['regionData']:
            if region['settingsHash'] == regionHash: return region.get('name')
    except:
        return None

def sendNotificationRegion(planetIndex, filteredAttr, hash):

    gifURL = None
    filteredLines = []
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    
    planetName = getPlanetName(int(planetIndex))
    regionName = getRegionName(hash)

    if not isinstance(planetName, str): return ("ERROR, NAME NOT FOUND")
    if not isinstance(regionName, str): return ("ERROR, NAME NOT FOUND")
    title = "🚨 REGION CHANGE DETECTED!"
    filteredLines.append(f"**\nPLANET NAME: {planetName}**\n")
    filteredLines.append(f"**\nREGION NAME: {regionName}**\n")

    for attr, difference in filteredAttr.items():

        if attr == 'owner':
            oldName = factionNames.get(str(difference['old']))
            newName = factionNames.get(str(difference['new']))
            gifURL = gifsOwner.get(str(difference['new']))
            if oldName == None: 
                title = "NEW REGION DETECTED!"
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
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP} HP:  %{(decayNew):.2f}/h**\n")
            else:
                decayOld = ((oldRegen*3600) / maxHP) * 100
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY RELATIVE TO {maxHP} HP:  %{(decayOld):.2f}/h  ➜  %{(decayNew):.2f}/h**\n")

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
                filteredLines.append(f"**AVAILABLE:  {newAvailable}\n**")
            else:
                filteredLines.append(f"**AVAILABLE:  {oldAvailable} ➜ {newAvailable}\n**")

    filteredText = "\n".join(filteredLines)

    if gifURL:createEmbed(title, filteredText, gifURL, timestamp)
    else: createEmbed(title, filteredText, imgURL, timestamp)

def sendNotificationPlanet(planetIndex, filteredAttr):
    
    gifURL = None
    filteredLines = []
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()
    planetName = getPlanetName(int(planetIndex))
    if not isinstance(planetName, str): return ("ERROR, NAME NOT FOUND")

    title = "🚨 PLANET CHANGE DETECTED!"
    filteredLines.append(f"**\nPLANET NAME: {planetName}**\n")

    for attr, difference in filteredAttr.items():

        if attr == 'owner':
            oldName = factionNames.get(str(difference['old']))
            newName = factionNames.get(str(difference['new']))
            gifURL = gifsOwner.get(str(difference['new']))
            filteredLines.append(f"**{attr.upper()}: {oldName.upper()} ➜ {newName.upper()}**\n")

        elif attr == 'regenPerSecond':
            oldRegen = difference['old']
            newRegen = difference['new']
            for planet in apiStuff.get("planetData"):
                if planet['index'] == planetIndex:
                    maxHP = planet['maxHealth']
                    break
            
            if oldRegen == None:
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY: %{(decayNew):.3f}**\n")
            else:
                decayOld = ((oldRegen*3600) / maxHP) * 100
                decayNew = ((newRegen*3600) / maxHP) * 100
                filteredLines.append(f"**DECAY: %{(decayOld):.3f} ➜ %{(decayNew):.3f}**\n")
        
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
                    filteredLines.append(f"**WARP LINK ADDED FROM {planetName} TO {planetNameWarpOld}**\n")
        
        elif attr == 'galacticEffectId':
            oldEffects = difference['old'] or []
            newEffects = difference['new'] or []

            for effectIDNew in newEffects:
                if effectIDNew not in oldEffects:
                    filteredLines.append(f"**EFFECT {effectIDNew} ADDED**\n")

            for effectIDOld in oldEffects:
                if effectIDOld not in newEffects:
                    filteredLines.append(f"**EFFECT {effectIDOld} REMOVED**\n")

        else: filteredLines.append(f"**{attr.upper()}: {difference['old']} ➜ {difference['new']}**\n")

    filteredText = "\n".join(filteredLines)
    
    if gifURL:createEmbed(title, filteredText, gifURL, timestamp)
    else: createEmbed(title, filteredText, imgURL, timestamp)

def sendNotificationEvent(hasEnded, event, deviation):

    gifURL = None
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if not hasEnded:

        expiresAt = event.get("expireTime")
        startedAt = event.get("startTime")
        defenseLevel = int(event.get("maxHealth")) / 50000
        race = event.get("race")
        typeEvent = eventTypes.get(str(event.get("eventType")))
        pIndex = event.get("planetIndex")
        faction = factionNames.get(str(race))
        startedAtAtReal = startTimeConstant + startedAt + deviation
        expiresAtReal = startTimeConstant + expiresAt + deviation
        planetAttacks = apiStuff.get("planetAttacks", [])
        attackList = []

        if str(pIndex) in planet_names: pName = planet_names.get(str(pIndex))
        if not isinstance(faction, str): return ("ERROR, NAME NOT FOUND")
        if not isinstance(typeEvent, str): return ("ERROR, NAME NOT FOUND")
        gifURL = gifsOwner.get(str(race))
        
        for planet in planetAttacks:
            sourceID = planet.get("source")
            targetID = planet.get("target")
            if pIndex == targetID:
                if str(sourceID) in planet_names: 
                    pNameSource = planet_names.get(str(sourceID))
                    attackList.append(pNameSource)
                    attackText = " ".join(attackList)
                break
        title = "🚨 PLANET EVENT STARTED!"
        descriptionList = []
        descriptionList.append(f"**\nPLANET NAME: {pName}**\n")
        descriptionList.append(f"**\nEVENT TYPE: {typeEvent.upper()}**\n")
        descriptionList.append(f"**\nPLANET ATTACKED BY THE: {faction.upper()}**\n")
        descriptionList.append(f"**\nATTACK SOURCE(S): {attackText}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} LEVEL: {int(defenseLevel)}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} TOTAL HP: {int(defenseLevel)*50000}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} STARTED**: <t:{startedAtAtReal}>\n")
        descriptionList.append(f"**\n{typeEvent.upper()} ENDS**: <t:{expiresAtReal}>\n")
        descriptionText = "\n".join(descriptionList)

        createEmbed(title, descriptionText, gifURL, timestamp)


    if hasEnded:
        race = event.get("race")
        pIndex = event.get("planetIndex")
        typeEvent = eventTypes.get(str(event.get("eventType")))
        faction = factionNames.get(str(race))
        currentPlanetData = deepcopy(apiStuff["planetData"])
        hasLost = True

        for currentPlanet in currentPlanetData:
            if pIndex == currentPlanet['index']:
                currentOwner = currentPlanet['owner']
                if race != currentOwner: hasLost = False
                break
     
        if str(pIndex) in planet_names: pName = planet_names.get(str(pIndex))
        if not isinstance(faction, str): faction = ("name not found")
        if not isinstance(typeEvent, str): typeEvent = ("name not found")

        title = "🚨 PLANET EVENT ENDED!"
        descriptionList = []
        descriptionList.append(f"**\nPLANET NAME: {pName}**\n")
        descriptionList.append(f"**\nEVENT TYPE: {typeEvent.upper()}**\n")
        descriptionList.append(f"**\nPLANET ATTACKED BY THE: {faction.upper()}**\n")
        descriptionList.append(f"**\nATTACK SOURCE(S): {attackText}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} LEVEL: {int(defenseLevel)}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} TOTAL HP: {int(defenseLevel)*50000}**\n")
        descriptionList.append(f"**\n{typeEvent.upper()} STARTED**: <t:{startedAtAtReal}>\n")
        descriptionList.append(f"**\n{typeEvent.upper()} ENDS**: <t:{expiresAtReal}>\n")
        if hasLost:
            gifURL = gifsOwner.get(str(race))
            descriptionList.append(f"\n**THE HELLDIVERS HAVE LOST THE {typeEvent.upper()} TO {faction.upper()}**")

        if not hasLost:
            gifURL = gifsOwner.get(str(currentOwner))
            descriptionList.append(f"\n**THE HELLDIVERS HAVE WON THE {typeEvent.upper()} AGAINST THE {faction.upper()}**")

        descriptionText = "\n".join(descriptionList)

        createEmbed(title, descriptionText, gifURL, timestamp)

def sendNotificationDSS(newPIndex, oldPIndex, newEffects, oldEffects):

    timestamp = dt.now(pytz.timezone("UTC")).isoformat()
    if str(oldPIndex) in planet_names: oldName = planet_names.get(str(oldPIndex))
    else: return ("ERRO, NO NAME")
    if str(newPIndex) in planet_names: newName = planet_names.get(str(newPIndex))
    else: return ("ERRO, NO NAME")
    textList = []
    if not newPIndex == oldPIndex:
        textList.append(f"**\nDSS HAS WARPED FROM {oldName.upper()} ➜ {newName.upper()}**\n")
    
    if not newEffects == oldEffects:
        
        for effectIDNew in newEffects:
            if effectIDNew not in oldEffects:
                
                if str(effectIDNew) in actionsDSS:
                    effectNameNew = actionsDSS[str(effectIDNew)]
                    textList.append(f"**EFFECT {effectNameNew.upper()} ({effectIDNew}) ADDED**\n")
                else:textList.append(f"**EFFECT {effectIDNew} ADDED**\n")
                
        for effectIDOld in oldEffects:
            if effectIDOld not in newEffects:

                if str(effectIDOld) in actionsDSS:
                    effectNameOld = actionsDSS[str(effectIDOld)]
                    textList.append(f"**EFFECT {effectNameOld.upper()} ({effectIDOld}) ENDED**\n")
                else:textList.append(f"**EFFECT {effectIDOld} ENDED**\n")
                
    title = "🚨 DSS UPDATED!"
    textDescription = "".join(textList)
    createEmbed(title, textDescription, dssGif, timestamp)

def sendNotificationGenInfo(oldData):
    oldGenInfo = deepcopy(oldData.get('generalInfo', []))
    newGenInfo = deepcopy(apiStuff.get('generalInfo', []))
    
    if newGenInfo == oldGenInfo: return

    newLayout = newGenInfo["layoutVersion"]
    oldLayout = oldGenInfo["layoutVersion"]
    newStoryID = newGenInfo["storyBeatId32"]
    oldStoryID = oldGenInfo["storyBeatId32"]

    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    changes = []
    title = "🚨 GENERAL INFO UPDATED!"
    if oldLayout != newLayout: changes.append(f"**LAYOUT VERSION: {oldLayout} ➜ {newLayout}**")
    if oldStoryID != newStoryID: changes.append(f"**STORY BEAT ID: {oldStoryID} ➜ {newStoryID}**")
    if not changes: return

    description = "\n".join(changes)

    createEmbed(title, description, imgURL, timestamp)

def sendNotificationCampaign(oldData):
    oldCampaign = deepcopy(oldData.get("campaignData", []))
    newCampaign = deepcopy(apiStuff.get("campaignData", []))
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    if oldCampaign == newCampaign: return
    descriptionLines = []
    oldDict = {campaign["id"]: campaign for campaign in oldCampaign}
    newDict = {campaign["id"]: campaign for campaign in newCampaign}

    oldIDs = set(oldDict.keys())
    newIDs = set(newDict.keys())

    hasEndedIDs = oldIDs - newIDs
    hasStartedIDs = newIDs - oldIDs
    equalIDs = oldIDs & newIDs

    for campaignId in hasEndedIDs:
        campaign = oldDict[campaignId]
        pIndexOld = campaign.get("planetIndex")
        pCampaignTypeOld = campaign.get("type")
        pCampaignNameOld = campaignTypes.get(str(pCampaignTypeOld))
        pNameOld = getPlanetName(int(pIndexOld))
        descriptionLines.append(f"**{pCampaignNameOld.upper()} CAMPAIGN ON {pNameOld.upper()} HAS ENDED**\n")

    for campaignId in hasStartedIDs:
        campaign = newDict[campaignId]
        pIndexNew = campaign.get("planetIndex")
        pCampaignTypeNew = campaign.get("type")
        pCampaignNameNew = campaignTypes.get(str(pCampaignTypeNew))
        pNameNew = getPlanetName(int(pIndexNew))
        descriptionLines.append(f"**{pCampaignNameNew.upper()} CAMPAIGN ON {pNameNew.upper()} HAS STARTED**\n")

    for campaignId in equalIDs:
        oldCamp = oldDict[campaignId]
        newCamp = newDict[campaignId]
        pName = getPlanetName(int(newCamp["planetIndex"]))

        if oldCamp["type"] != newCamp["type"]:
            oldType = campaignTypes[str(oldCamp["type"])] 
            newType = campaignTypes[str(newCamp["type"])] 
            descriptionLines.append(f"**CAMPAIGN ON {pName.upper()} CHANGED FROM {oldType.upper()}  ➜  {newType.upper()}**\n")
                
    descriptionText = "\n".join(descriptionLines)
    title = "🚨 GENERAL INFO UPDATED!"

    createEmbed(title, descriptionText, imgURL, timestamp)

def sendNotificationGlobalEvent(oldData):
    oldGlobal = deepcopy(oldData.get("globalEvents", []))
    newGlobal = deepcopy(apiStuff.get("globalEvents", []))
    timestamp = dt.now(pytz.timezone("UTC")).isoformat()

    newGlobalDict = {globalEvent["eventId"]: globalEvent for globalEvent in newGlobal}
    oldGlobalDict = {globalEvent["eventId"]: globalEvent for globalEvent in oldGlobal}

    oldIDs = set(oldGlobalDict.keys())
    newIDs = set(newGlobalDict.keys())

    descriptionLines = []
    hasEndedIDs = oldIDs - newIDs
    hasStartedIDs = newIDs - oldIDs
    updated = False

    for globalEventID in hasEndedIDs:
        globalEventEnded = oldGlobalDict[globalEventID]
        title = (f"🚨GLOBAL EVENT ENDED")
        message = globalEventEnded.get("message")
        descriptionLines.append(message)
        updated = True
    
    for globalEventID in hasStartedIDs:
        globalEventStarted = newGlobalDict[globalEventID]
        title = (f"🚨GLOBAL EVENT STARTED")
        message = globalEventStarted.get("message")
        descriptionLines.append(message)
        gametime = apiStuff["generalInfo"].get("time")
        expiresAt = globalEventStarted.get("expireTime")
        unixNow = int(dt.now().timestamp())
        deviation =  unixNow - (startTimeConstant + gametime)
        expiresAtReal = startTimeConstant + expiresAt + deviation
        descriptionLines.append(f"**\nGLOBAL EVENT ENDS**: <t:{expiresAtReal}>\n")
        updated = True
    
    if updated:
        descriptionText = "\n".join(descriptionLines)
        createEmbed(title, descriptionText, imgURL, timestamp)

    else: return

def shouldNotifyPlanet(planetIndex, filteredAttr):

    key = planetIndex

    filter = {attr: value["new"] for attr, value in filteredAttr.items()}
    
    if lastNotifiedPlanet.get(key) != filter:
        lastNotifiedPlanet[key] = filter
        return True
    
    return False

def shouldNotifyRegion(planetIndex,regionIndex, filteredAttr):

    key = f"{planetIndex}_{regionIndex}"

    filter = {attr: value["new"] for attr, value in filteredAttr.items()}

    if lastNotifiedRegion.get(key) != filter:
        lastNotifiedRegion[key] = filter
        return True
    
    return False
    
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
            pIndex, rIndex = keyStr.split("_")
            
            if filteredAttr and shouldNotifyRegion(pIndex, rIndex, filteredAttr):
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
                regionHealthChanges[regionID] = {"changes": filterHealth}

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

            if filteredAttr and shouldNotifyPlanet(index, filteredAttr):
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
                planetHealthChanges[planetID] = {"changes": filterHealth}

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

    #if oldEvents == newEvents: return

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

    staticRequest = requests.get(urlWarinfo) # Me: Pega as informações da API Warinfo
    if staticRequest.status_code == 200:
        staticData = staticRequest.json() # Me: Copia todas as informações pra essavariável
    else:
        print(f"Failed to retrieve API data {staticRequest.status_code}.")
        time.sleep(4)
        return 
    
    statusRequest = requests.get(urlStatus) # Me: Repete a mesma coisa aqui
    if statusRequest.status_code == 200:
        statusData = statusRequest.json() # Me: e aqui
    else:
        print(f"Failed to retrieve API data {statusRequest.status_code}.")
        time.sleep(4)
        return 

    staticRequest = None
    statusRequest = None

    staticPlanet = [deepcopy(planetStatic) for planetStatic in staticData['planetInfos']] # Me: Pega as informações específica de planetInfos
    statusPlanet = [deepcopy(planetStatus) for planetStatus in statusData['planetStatus']] # Me: Específica de planetStatus
    staticRegion = [deepcopy(regionStatic) for regionStatic in staticData['planetRegions']] # Me: As informações das regiões na API estática
    statusRegion = [deepcopy(regionStatus) for regionStatus in statusData['planetRegions']] # Me: Informações da API status
    
    staticMapPlanet = {planet['index']: planet for planet in staticPlanet} # Me: Pra fazer um mapa (o index vai ser o id do planeta e vai ter as informações)
    statusMapPlanet = {planet['index']: planet for planet in statusPlanet} # Me: Mapa do status, mesma ideia do de cima

    for key, status in statusMapPlanet.items(): # Me: Aqui vai pegar a chave do indexador (id do planeta) e as informações dentro
        if key in staticMapPlanet: # Me: Vai verificar se existe no mapa estático
            combinePlanets = deepcopy(staticMapPlanet[key]) # Me: Se existir vai copiar as informações do planeta que tá em estático pra essa variável
            for attr, value in status.items(): # Me: Pega os atributos dos planeta que tá na api status e o valor
                if attr == 'health':
                    if combinePlanets['maxHealth'] < value:
                        combinePlanets['maxHealth'] = value; combinePlanets['health'] = value

                    else: combinePlanets['health'] = value
                else:
                    if attr not in combinePlanets: 
                        combinePlanets[attr] = value # Me: Se for um atributo novo, vai adicionar o atributo
                    else: 
                        if combinePlanets[attr] != value: combinePlanets[attr] = value # Me: Caso já tenha e o atributo for um valor diferente, vai atualizar
                
            staticMapPlanet[key] = combinePlanets # Me: Adiciona o planeta com os atributos atualizados e novos pro mapa estático
    
    planetActiveEffects = statusData.get("planetActiveEffects", [])
    effectsGrouped = {}
    for effect in planetActiveEffects:
        effectPIndex = effect.get('index')
        effectID = effect.get('galacticEffectId')

        if effectPIndex not in effectsGrouped:
            effectsGrouped[effectPIndex] = []

        effectsGrouped[effectPIndex].append(effectID)
    
    for planetIndex, _ in staticMapPlanet.items(): # Me: só pega o index do planeta
        if str(planetIndex) in planet_names: staticMapPlanet[planetIndex]['name'] = planet_names[str(planetIndex)] # Me: Adiciona o nome
        staticMapPlanet[planetIndex]['galacticEffectId'] = effectsGrouped.get(planetIndex, [])
        
    staticMapRegion = {(region['planetIndex'], region['regionIndex']): region for region in staticRegion}
    statusMapRegion = {(region['planetIndex'], region['regionIndex']): region for region in statusRegion}
    # Me: Repete o processo pra região, mas como tem id do planeta e id da região, a chave vira uma tupla
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
        if str(regionHash) in planetRegionData: staticMapRegion[tupla]['name'] = planetRegionData[str(regionHash)]['name']
    
    apiStuff["planetData"] = list(staticMapPlanet.values()) # Me: Copia todos valores combinados
    apiStuff["planetEvents"] = statusData.get("planetEvents", [])
    apiStuff['planetActiveEffects'] = statusData.get("planetActiveEffects", [])
    apiStuff["regionData"] = list(staticMapRegion.values()) # Me: Copia todos os valores combinados e não fica uma tupla
    apiStuff['planetAttacks'] = statusData.get("planetAttacks", [])
    apiStuff['campaignData'] = statusData.get("campaigns", [])
    apiStuff['spaceStations'] = statusData.get("spaceStations", [])
    apiStuff['globalEvents'] = statusData.get("globalEvents", [])
    apiStuff['generalInfo'] = {
        "startDate": staticData.get("startDate"),
        "time": statusData.get("time"),
        "impactMultiplier": statusData.get("impactMultiplier"),
        "layoutVersion": statusData.get("layoutVersion"),
        "storyBeatId32": statusData.get("storyBeatId32"),
    }

def main():

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
            sendNotificationCampaign(oldData)
            updateDSS(oldData)
            sendNotificationGenInfo(oldData)
            sendNotificationGlobalEvent(oldData)
        
        saveAPIData()

if __name__ == "__main__":
    main()