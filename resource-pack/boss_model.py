"""Original voxel-built mountain Yeti based on the supplied gorilla-like reference."""
import math
COLORS={'fur':(210,222,226,255),'fur_light':(238,246,246,255),'fur_shadow':(164,182,190,255),
 'frost':(184,210,220,255),'frost_dark':(93,121,133,255),'frost_light':(215,238,245,255),
 'face':(80,103,110,255),'mouth':(40,16,23,255),'tongue':(125,40,48,255),
 'tooth':(221,247,250,255),'eye':(247,42,38,255),'eye_shadow':(116,25,29,255)}
def model(frame=None,attack=None):
 cells={}
 def box(a,b,material,part='body'):
  for x in range(a[0],b[0]):
   for y in range(a[1],b[1]):
    for z in range(a[2],b[2]):cells[x,y,z]=(material,part)
 # 32-voxel construction, exported at half-unit resolution.
 box((8,10,13),(24,23,25),'fur')
 box((10,13,12),(22,21,13),'fur')
 box((1,7,12),(8,23,23),'fur','arm_l')
 box((24,7,12),(31,23,23),'fur','arm_r')
 box((0,4,10),(8,10,23),'frost_dark','arm_l')
 box((24,4,10),(32,10,23),'frost_dark','arm_r')
 # Individual fingers and icy claws instead of square mittens.
 for x in (0,2,4,6):
  box((x,2,10),(x+1,6,13),'face','arm_l')
  box((x,2,9),(x+1,3,10),'tooth','arm_l')
  box((24+x,2,10),(25+x,6,13),'face','arm_r')
  box((24+x,2,9),(25+x,3,10),'tooth','arm_r')
 box((9,0,13),(15,12,24),'fur','leg_l')
 box((17,0,13),(23,12,24),'fur','leg_r')
 box((9,0,10),(15,3,24),'frost_dark','leg_l')
 box((17,0,10),(23,3,24),'frost_dark','leg_r')
 box((11,21,7),(23,32,21),'fur')
 # Deep mouth: remove fur from the opening, leaving a dark recessed back.
 for x in range(13,21):
  for y in range(23,28):
   for z in range(6,16):cells.pop((x,y,z),None)
 box((13,23,15),(21,28,16),'mouth')
 box((13,22,6),(21,23,16),'face')
 box((12,23,6),(13,28,16),'face');box((21,23,6),(22,28,16),'face')
 box((13,28,6),(21,29,10),'face')
 box((14,23,10),(20,24,15),'tongue')
 for x in (13,15,18,20):
  depth=3 if x in (13,20) else 1
  box((x,28-depth,6),(x+1,28,8),'tooth')
  box((x,23,6),(x+1,24,8),'tooth')
 # Recessed red eyes under a heavy brow, small squared muzzle.
 box((12,29,6),(16,31,7),'eye_shadow');box((18,29,6),(22,31,7),'eye_shadow')
 box((13,29,5),(15,30,6),'eye');box((19,29,5),(21,30,6),'eye')
 box((11,31,5),(16,32,8),'fur_light');box((18,31,5),(23,32,8),'fur_light')
 box((15,28,4),(19,30,7),'face')
 box((15,29,3),(16,30,4),'mouth');box((18,29,3),(19,30,4),'mouth')
 # Stepped fur fringe on shoulders, cheeks and jaw, without protruding horns.
 for x in (1,3,5,25,27,29):
  part='arm_l' if x<8 else 'arm_r'
  box((x,23,14),(x+2,24,21),'fur_light',part)
  box((x,17,11),(x+1,20,12),'fur',part)
 for x in (10,22):box((x,24,7),(x+1,30,9),'fur_light')
 for x in (12,15,18,21):box((x,20,8),(x+1,23,10),'fur_light')
 for (x,y,z),(material,part) in list(cells.items()):
  noise=(x*7+(y//2)*5+z*11)%23
  if material=='fur':
   if noise<4:material='fur_shadow'
   elif noise>17:material='fur_light'
   elif noise==10:material='frost'
  cells[x,y,z]=(material,part)
 directions={'west':(-1,0,0),'east':(1,0,0),'down':(0,-1,0),'up':(0,1,0),'north':(0,0,-1),'south':(0,0,1)}
 pivots={'arm_l':[2,9,8.5],'arm_r':[14,9,8.5],'leg_l':[6.5,5,8.5],'leg_r':[10.5,5,8.5]}
 elements=[]
 for (x,y,z),(material,part) in sorted(cells.items()):
  faces={}
  for face,(dx,dy,dz) in directions.items():
   neighbor=cells.get((x+dx,y+dy,z+dz))
   if neighbor is None or neighbor[1]!=part:faces[face]={'uv':[0,0,16,16],'texture':'#'+material}
  if not faces:continue
  e={'from':[x/2,y/2,z/2],'to':[(x+1)/2,(y+1)/2,(z+1)/2],'faces':faces}
  if part in pivots and (frame is not None or attack is not None):
   if part.startswith('arm'):
    angle=-45*math.sin(math.pi*attack/7) if attack is not None else -18*(1-4*abs((frame/12+.25)%1-.5))
   else:angle=0 if attack is not None else 25*math.sin(2*math.pi*frame/12)*(1 if part=='leg_l' else -1)
   angle=round(angle/22.5)*22.5
   e['rotation']={'origin':pivots[part],'axis':'x','angle':angle,'rescale':False}
  elements.append(e)
 return {'credit':'Original mountain Yeti inspired by the supplied visual reference.',
         'textures':{name:'yetiboss:boss/'+name for name in COLORS},'elements':elements,
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
