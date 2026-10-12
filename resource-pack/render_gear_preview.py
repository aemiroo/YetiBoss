import sys,json,io
import pathlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from gear_model import model,texture
from mesh_preview import raster
from PIL import Image,ImageDraw,ImageFont
im=Image.new('RGB',(1440,800),(24,31,43));d=ImageDraw.Draw(im);f='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';d.text((35,25),'IMPORTED FROST GEAR',font=ImageFont.truetype(f,28),fill='white');d.text((35,68),'Original supplied geometry and textures • converted model preview',font=ImageFont.truetype(f,17),fill=(160,185,208))
for i,(n,label) in enumerate([('frostfang','Ice Sword'),('frostpickaxe','Ice Pickaxe'),('frostbow','Frost Bow')]):
 m=model(n);tile=Image.frombytes('RGBA',(460,620),raster(m,{k:texture(k) for k in m['textures']},460,620,37));im.paste(tile,(10+i*480,110),tile);d.text((35+i*480,750),label,font=ImageFont.truetype(f,22),fill='white')
im.save(sys.argv[1])
