import config
import logs

import pymongo

client = None
database = None

def connect():
    global client
    global database
    global settings
    logs.info("Connecting to the MongoDB service...")
    if config.config['db-auth']:
        client = pymongo.MongoClient(f"mongodb://{config.config['db-user']}:{config.config['db-pass']}@{config.config['db-host']}:{config.config['db-port']}/")
    else:
        client = pymongo.MongoClient(f"mongodb://{config.config['db-host']}:{config.config['db-port']}/")
    database = client[config.config['db-name']]
    logs.info("Connected to database!")
    logs.log("Database version " + client.server_info()["version"])

# unique ids
def new_id():
    misc = database["misc"]
    misc.find_one_and_update({}, {'$inc': {'id': 1}},upsert=True)
    return misc.find_one()["id"]

# user data
def fetch_user(id):
    users = database["users"]
    return users.find_one({"id":id})

def set_timezone(id, timezone):
    users = database["users"]
    users.find_one_and_update({"id":id}, {'$set': {'timezone': timezone}},upsert=True)

def set_pronouns(id, pronouns):
    users = database["users"]
    users.find_one_and_update({"id":id}, {'$set': {'pronouns': pronouns}},upsert=True)

# prefixes

def fetch_global_prefixes():
    settings = database["settings"]
    return settings.find_one()["prefixes"]

def add_global_prefix(prefix):
    settings = database["settings"]
    settings.find_one_and_update({},{'$push': {'prefixes': prefix}},upsert=True)

def remove_global_prefix(prefix):
    settings = database["settings"]
    settings.find_one_and_update({},{'$pull': {'prefixes': prefix}},upsert=True)

# warnings

def fetch_warnings(user_id, guild_id):
    warnings = database["warnings"]
    return list(warnings.find({"user_id": user_id, "guild_id": guild_id}))

def add_warning(warning):
    warnings = database["warnings"]
    warnings.insert_one(warning)

def remove_warning(to_remove):
    warnings = database["warnings"]
    warnings.delete_one({"id": to_remove})

def fetch_warning(id):
    warnings = database["warnings"]
    return warnings.find_one({"id": id})

# mutes

def fetch_timed_mute(user_id):
    mutes = database["mutes"]
    return mutes.find_one({"user_id": user_id})

def fetch_timed_mutes():
    mutes = database["mutes"]
    mutes_dict = {}
    for mute in mutes.find():
        mutes_dict[mute["id"]] = mute
    return mutes_dict

def remove_timed_mute(user_id):
    mutes = database["mutes"]
    mutes.delete_one({"user_id": user_id})

def add_timed_mute(mute):
    mutes = database["mutes"]
    mutes.insert_one(mute)


# reminders

def fetch_reminders():
    reminders = database["reminders"]
    reminders_dict = {}
    for reminder in reminders.find():
        reminders_dict[reminder["id"]] = reminder
    return reminders_dict

def remove_reminder(to_remove):
    reminders = database["reminders"]
    reminders.delete_one({"id": to_remove})

def add_reminder(reminder):
    reminders = database["reminders"]
    reminders.insert_one(reminder)

# restarted message

def fetch_restarted_info():
    restart = database["restart"]
    return restart.find_one()

def add_restarted_info(info):
    restart = database["restart"]
    restart.insert_one(info)

def clear_restarted_info():
    restart = database["restart"]
    restart.delete_one({})

def close():
    logs.info("Closing connection to MongoDB...")
    if client:
        client.close()
