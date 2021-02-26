import discord
import database

def has_pronouns(id):
    user_data = database.fetch_user(id)
    if (not user_data) or (not user_data.get("pronouns")):
        return False
    else:
        return True

def get_user_pronouns(id):
    user_data = database.fetch_user(id)
    if (not user_data) or (not user_data.get("pronouns")):
        return {
            "subject": "they",
            "object": "them",
            "pos_determiner": "their",
            "pos_pronoun": "theirs",
            "plural": True
        }
    else:
        return user_data["pronouns"]

def match_input(iterable, objtype, request):
	"""Return a member/guild/channel/role/emoji object given an input which could be anything
	that identifies that object. If it can't be found, return None.

	iterable: The iterable to search through.

	objtype: A discord.py class that specifies the type of object to search for. Can be either
	discord.Member, discord.Guild, discord.abc.GuildChannel, discord.Role, or discord.Emoji.
	Note that this function doesn't actually use isinstance() or do any type-checking with this,
	this just specifies which attributes to check for, kind of like an enum.

	request: A string that will be tried to be matched to.

	It is recommended you filter out unneeded objects from `iterable` when using this function.

	The following priority is used:
	1) (Members only) Mention: <@146814960574398464> or <@!146814960574398464>
	2) (Channels only) Mention: <#153368829160849408>
	3) (Roles only) Mention: <@&153369506813706240>
	4) (Emojis only) Emoji: <:unjoy:263889385492185088>
	5) ID: 146814960574398464
	6) (Members only) Username/Username+Discriminator (Discord tag)/Nickname, whatever
	discord.Guild.get_member_named() accepts: Info Teddy, Info Teddy#3737, info teddy
	7) Name: tOLP, general, Owner, unjoy
	8) (Members only) Case-insensitive nickname complete match: info teddy
	9) Case-insensitive name complete match: Info Teddy, tolp, owner
	10) (Members only) Case-insensitive nickname partial match: info
	11) Case-insensitive name partial match: Info, tOL, own
	12) (Members only) Discriminator only (either with or without #): 3737
	"""
	acceptvals = (
		discord.Member,
		discord.Guild,
		discord.abc.GuildChannel,
		discord.Role,
		discord.Emoji,
	)
	if objtype not in acceptvals:
		raise ValueError('objtype has to be one of ' + str(acceptvals))

	target = None
	int_request = None

	# If nothing was specified, then we're done quickly.
	if request is None:
		return None

	# Is this a mention, or an emoji? If so, extract the ID from it
	if request.startswith('<') and request.endswith('>'):
		if (objtype is discord.Member and request[1:3] == '@!') or \
		(objtype is discord.Role and request[1:3] == '@&'):
			int_request = int(request[3:-1])
		elif (objtype is discord.Member and request[1] == '@') or \
		(objtype is discord.abc.GuildChannel and request[1] == '#'):
			int_request = int(request[2:-1])
		elif objtype is discord.Emoji and request[1] == request[-20] == ':':
			int_request = int(request[-19:-1])
	elif request.isdigit() and len(request) != 4:
		int_request = int(request)

	# Now get the object from the ID (if we got any)
	if int_request is not None:
		target = discord.utils.find(lambda x: x.id == int_request, iterable)

	if target is not None:
		return target

	# We're still executing, so we didn't get an ID
	if objtype is discord.Member:
		# Not my problem
		return match_member_attrs(iterable, request)

	# Every other type here

	namematched = None
	namefound = None

	for obj in iterable:
		if obj.name is None:
			continue
		if obj.name.lower() == request.lower():
			namematched = obj
			break
		if obj.name.lower().find(request.lower()) != -1:
			namefound = obj
			break

	target = namematched if namematched else namefound

	return target

def match_member_attrs(iterable, request):
	"""Return a discord.Member object from an iterable of discord.Member objects, given a
	string that could match the object in any way.

	This is a match_input() helper function.

	The following priority is used:
	1) Username/Username+Discriminator (Discord tag)/Nickname, whatever
	discord.Guild.get_member_named() accepts: Info Teddy, Info Teddy#3737, info teddy
	2) Name: tOLP, general, Owner, unjoy
	3) Case-insensitive nickname complete match: info teddy
	4) Case-insensitive name complete match: Info Teddy, tolp, owner
	5) Case-insensitive nickname partial match: info
	6) Case-insensitive name partial match: Info, tOL, own
	7) Discriminator only (either with or without #): 3737
	"""
	# Let's be flexible
	if not isinstance(iterable, list):
		iterable = list(iterable)

	# Let's create an object close to a discord.Guild, so we
	# can use discord.Guild.get_member_named()
	class DuckTypedGuild:  # pylint: disable=too-few-public-methods
		members = []
	dt_guild = DuckTypedGuild()

	# Let's create an object close to a discord.Member, so we
	# can actually use discord.Guild.get_member_named()
	# if we want to use User objects
	# without pulling our fucking hair out
	class DuckTypedMember: # pylint: disable=too-few-public-methods
		def __init__(self, actual_member):
			self.id = actual_member.id
			self.nick = None
			self.name = actual_member.name
			self.discriminator = actual_member.discriminator

	for idx, member in enumerate(iterable):
		if not hasattr(member, 'nick'):
			iterable[idx] = DuckTypedMember(member)

	dt_guild.members = iterable

	target = discord.Guild.get_member_named(dt_guild, request)

	if target is not None:
		return target

	# Not found by guild.get_member_named()

	# Everything else fails? Then try searching.
	# Nicknames have priority, then usernames.
	# Maybe we're entering just a discriminator, match those as well.
	nickmatched = None
	usermatched = None
	nickfound = None
	userfound = None
	discmatched = None

	for member in dt_guild.members:
		if member.nick and member.nick.lower() == request.lower():
			nickmatched = member
			break
		if member.name.lower() == request.lower():
			usermatched = member
			break
		if member.nick and member.nick.lower().find(request.lower()) != -1:
			nickfound = member
			break
		if member.name.lower().find(request.lower()) != -1:
			userfound = member
			break
		if member.discriminator == request or \
		(request.startswith('#') and \
		member.discriminator == request[1:]):
			discmatched = member
			break

	target = nickmatched if nickmatched is not None else \
	usermatched if usermatched is not None else \
	nickfound if nickfound is not None else \
	userfound if userfound is not None else \
	discmatched

	return target
