from common import command
import PIL
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
import discord
import math
import re

async def dovtext(passedargs,scr):
    colors = {
        "gray":(174,174,174),
        "grey":(174,174,174),
        "cyan":(164,164,255),
        "viridian":(164,164,255),
        "red":(255,60,60),
        "vermilion":(255,60,60),
        "green":(144,255,144),
        "verdigris":(144,255,144),
        "yellow":(229,229,120),
        "vitellary":(229,229,120),
        "blue":(95,95,255),
        "victoria":(95,95,255),
        "pink":(255,134,255),
        "purple":(255,134,255),
        "violet":(255,134,255),
        "orange":(255,130,20),
        "darkaquamarine": (19,174,174),
        "darkgreen": (19,60,60),
        "brightgreen": (19,255,144),
        "brightblue": (19,95,255),
        "aquamarine": (19,164,255),
        "lessbrightgreen": (19,255,134),
        "brightgreen2": (19,255,134),
        "brighterblue": (19,134,255)
    }
    if scr:
        colors.pop("orange")
    c2 = colors["gray"]
    inputtext=""
    tcol = "gray"
    if passedargs != None:
        args = passedargs.split(" ")
        if args[0].lower() in colors:
            tcol = args[0].lower()
            c2 = colors[args[0].lower()]
            inputtext = " ".join(map(str,args[1:]))
        elif re.match("^(#)?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", args[0]):
            if not scr:
                thingo = args[0].lstrip('#')
                lv = len(thingo)
                c2 = tuple(int(thingo[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
                args.pop(0)
                inputtext = " ".join(map(str,args))
            else:
                c2 = colors["gray"]
                inputtext=passedargs
        else:
            c2 = colors["gray"]
            inputtext=passedargs
    c1 = (math.floor(c2[0]/6),math.floor(c2[1]/6),math.floor(c2[2]/6))
    font = ImageFont.truetype("PetMe64.ttf", 8)
    im = Image.new("RGBA", (1,1), color=c1)
    draw = ImageDraw.Draw(im)
    w,h = draw.multiline_textsize(inputtext, font=font,spacing=2)
    im = im.resize((w+15,h+17))
    draw = ImageDraw.Draw(im)
    draw.multiline_text((7,8), inputtext,c2,font=font,spacing=2)
    draw.rectangle([(1,1),(w+13,h+15)], fill=None, outline=c2)
    draw.rectangle([(2,2),(w+12,h+14)], fill=None, outline=c2)
    draw.rectangle([(4,4),(w+10,h+12)], fill=None, outline=c2)
    temp = BytesIO()
    im.save(temp, format="png")
    temp.flush()
    temp.seek(0)
    dfile = discord.File(temp, filename='output.png')
    if not scr:
        return dfile
    else:
        lines = len(inputtext.split("\n"))
        colorconv = {
            "gray":"gray",
            "grey":"gray",
            "cyan":"cyan",
            "viridian":"cyan",
            "red":"red",
            "vermilion":"red",
            "green":"green",
            "verdigris":"green",
            "yellow":"yellow",
            "vitellary":"yellow",
            "blue":"blue",
            "victoria":"blue",
            "pink":"purple",
            "purple":"purple",
            "violet":"purple",
            "darkaquamarine": "gray",
            "darkgreen": "red",
            "brightgreen": "green",
            "brightblue": "blue",
            "aquamarine": "cyan",
            "lessbrightgreen": "yellow",
            "brightgreen2": "yellow",
            "brighterblue": "purple"
        }
        if tcol in ["darkaquamarine","darkgreen","brightgreen","brightblue","aquamarine","lessbrightgreen","brightgreen2","brighterblue"]:
            tcol = colorconv[tcol]
            t = """squeak({})
text({},0,0,{})
{}
createcrewman(-50,0,blue,0,faceleft)
speak_active""".format(tcol,tcol,lines,inputtext.replace("```",""))
        else:
            tcol = colorconv[tcol]
            t = """squeak({})
text({},0,0,{})
{}
speak_active""".format(tcol,tcol,lines,inputtext.replace("```",""))
        return (dfile,t)

@command()
async def vtext(client, message, **kwargs):
    dfile = await dovtext(kwargs["arguments"],False)
    await message.channel.send(file=dfile)

@command()
async def vtscr(client, message, **kwargs):
    dfile,t = await dovtext(kwargs["arguments"],True)
    await message.channel.send(f"```{t}```",file=dfile)
