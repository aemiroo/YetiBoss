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
 # Broad upper torso narrowing towards the hips.
 box((10,10,13),(22,16,25),'fur')
 box((8,16,13),(24,23,25),'fur')
 box((10,13,12),(22,21,13),'fur')
 # Sloping upper arms, tapered forearms, shoulders overlap torso at the joints.
 for y in range(7,24):
  inner=0 if y<11 else 1 if y<16 else 2 if y<20 else 3
  width=7 if y<16 else 8
  box((inner,y,12),(inner+width,y+1,23),'fur','arm_l')
  box((32-inner-width,y,12),(32-inner,y+1,23),'fur','arm_r')
 box((0,4,10),(7,10,23),'frost_dark','arm_l')
 box((25,4,10),(32,10,23),'frost_dark','arm_r')
 # Individual fingers and icy claws instead of square mittens.
 for x in (0,2,4,6):
  box((x,2,10),(x+1,6,13),'face','arm_l')
  box((x,2,9),(x+1,3,10),'tooth','arm_l')
  box((24+x,2,10),(25+x,6,13),'face','arm_r')
  box((24+x,2,9),(25+x,3,10),'tooth','arm_r')
 # Wide planted feet and slightly outward-stepped legs.
 for y in range(12):
  offset=0 if y<4 else 1 if y<8 else 2
  box((7+offset,y,13),(13+offset,y+1,24),'fur','leg_l')
  box((19-offset,y,13),(25-offset,y+1,24),'fur','leg_r')
 box((6,0,10),(13,3,24),'frost_dark','leg_l')
 box((19,0,10),(26,3,24),'frost_dark','leg_r')
 box((11,19,7),(23,32,21),'fur')
 # Deep mouth: remove fur from the opening, leaving a dark recessed back.
 for x in range(13,21):
  for y in range(21,28):
   for z in range(6,16):cells.pop((x,y,z),None)
 box((13,21,15),(21,28,16),'mouth')
 box((13,20,6),(21,21,16),'face')
 box((12,21,6),(13,28,16),'face');box((21,21,6),(22,28,16),'face')
 box((13,28,6),(21,29,10),'face')
 box((14,21,10),(20,22,15),'tongue')
 for x in (13,15,18,20):
  depth=4 if x in (13,20) else 2
  box((x,28-depth,6),(x+1,28,8),'tooth')
  box((x,21,6),(x+1,23,8),'tooth')
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
 for x in (12,15,18,21):box((x,18,8),(x+1,21,10),'fur_light')
 # Stepped fur ends extend the silhouette on the upper arms and back.
 for side in ('arm_l','arm_r'):
  for top in (19,15,11):
   outer=1 if top<16 else 2
   for yy in range(top-3,top):
    x=outer-1 if side=='arm_l' else 32-outer
    box((x,yy,15),(x+1,yy+1,20),'fur_light',side)
 for x in (9,12,19,22):box((x,20,25),(x+1,23,27),'fur_shadow')
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
 # Stepped fur ends extend the silhouette on the upper arms and back.
 for side in ('arm_l','arm_r'):
  for top in (19,15,11):
   outer=1 if top<16 else 2
   for yy in range(top-3,top):
    x=outer-1 if side=='arm_l' else 32-outer
    box((x,yy,15),(x+1,yy+1,20),'fur_light',side)
 for x in (9,12,19,22):box((x,20,25),(x+1,23,27),'fur_shadow')
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
