"""Animated preview rendered directly from the exported Father Yeti models."""
import sys,io
from PIL import Image,ImageDraw,ImageFont
from boss_model import model
from build_pack import png
from mesh_preview import raster
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
frames=[]
for i in range(12):
 canvas=Image.new('RGB',(900,440),(24,31,43));d=ImageDraw.Draw(canvas)
 d.text((24,16),'FATHER YETI — GORILLA STANCE DRAFT',font=ImageFont.truetype(font,22),fill=(230,241,249))
 d.text((24,48),'Actual exported geometry and textures • animation preview',font=ImageFont.truetype(font,14),fill=(161,185,205))
 for j,(label,m) in enumerate([('Idle',model()),('Walking',model(frame=i)),('Slam wind-up',model(attack=round(i*7/11)))]):
  textures={n:png(path.rsplit('/',1)[1]) for n,path in m['textures'].items()}
  tile=Image.frombytes('RGBA',(280,330),raster(m,textures,280,330,16,yaw=.43,center=(8,10,8)))
  canvas.paste(tile,(10+300*j,77),tile);d.text((24+300*j,409),label,font=ImageFont.truetype(font,17),fill=(218,234,245))
 frames.append(canvas)
frames[0].save(sys.argv[1],save_all=True,append_images=frames[1:],duration=110,loop=0,disposal=2)
frames[3].save('/tmp/father-preview-check.png')
