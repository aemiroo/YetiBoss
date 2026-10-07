"""Original block-built frost Yeti inspired by the user's blue-and-white reference."""
import math
COLORS={'fur':(219,235,243,255),'fur_light':(241,249,252,255),'fur_shadow':(174,201,217,255),
 'frost':(103,148,208,255),'frost_dark':(58,88,159,255),'frost_light':(154,198,237,255),
 'face':(70,99,166,255),'mouth':(64,37,62,255),'tooth':(239,232,202,255),
 'horn':(223,222,201,255),'horn_shadow':(179,181,162,255),'eye':(231,89,72,255),
 'ear':(133,69,91,255)}
def model(frame=None,attack=None):
 cells={}
 def box(a,b,material,part='body'):
  for x in range(a[0],b[0]):
   for y in range(a[1],b[1]):
    for z in range(a[2],b[2]):cells[x,y,z]=(material,part)
 box((4,3,6),(12,10,12),'fur')
 box((0,1,6),(4,10,11),'fur','arm_l')
 box((12,1,6),(16,10,11),'fur','arm_r')
 box((5,0,6),(8,4,11),'fur','leg_l')
 box((9,0,6),(12,4,11),'fur','leg_r')
 box((5,9,4),(11,14,10),'fur')
 # A blocky blue face with an open fang-filled mouth.
 box((5,9,3),(11,12,4),'face')
 box((5,10,3),(6,11,4),'eye');box((10,10,3),(11,11,4),'eye')
 box((6,9,3),(10,11,4),'mouth')
 for x in (6,8):box((x,10,3),(x+1,11,4),'tooth')
 for x in (7,9):box((x,9,3),(x+1,10,4),'tooth')
 box((4,11,4),(5,13,6),'ear');box((11,11,4),(12,13,6),'ear')
 # Thick upright cream horns with stepped outward tips.
 box((3,11,5),(5,15,7),'horn')
 box((11,11,5),(13,15,7),'horn')
 box((2,15,5),(4,16,7),'horn')
 box((12,15,5),(14,16,7),'horn')
 for (x,y,z),(material,part) in list(cells.items()):
  value=(x*7+(y//2)*5+z*11)%17
  if material=='fur':
   if part.startswith('arm') and y<5 or part.startswith('leg') and y<2:
    material='frost_dark' if value<5 else 'frost_light' if value>13 else 'frost'
   elif value<3:material='fur_shadow'
   elif value==7:material='fur_light'
   elif part.startswith(('arm','leg')) and value==12:material='frost_light'
  elif material=='horn' and value<5:material='horn_shadow'
  cells[x,y,z]=(material,part)
 directions={'west':(-1,0,0),'east':(1,0,0),'down':(0,-1,0),'up':(0,1,0),'north':(0,0,-1),'south':(0,0,1)}
 pivots={'arm_l':[2,9,8.5],'arm_r':[14,9,8.5],'leg_l':[6.5,3,8.5],'leg_r':[10.5,3,8.5]}
 elements=[]
 for (x,y,z),(material,part) in sorted(cells.items()):
  faces={}
  for face,(dx,dy,dz) in directions.items():
   neighbor=cells.get((x+dx,y+dy,z+dz))
   if neighbor is None or neighbor[1]!=part:faces[face]={'uv':[0,0,16,16],'texture':'#'+material}
  if not faces:continue
  e={'from':[x,y,z],'to':[x+1,y+1,z+1],'faces':faces}
  if part in pivots and (frame is not None or attack is not None):
   if part.startswith('arm'):
    angle=-40*math.sin(math.pi*attack/7) if attack is not None else -18*(1-4*abs((frame/12+.25)%1-.5))
   else:
    angle=0 if attack is not None else 25*math.sin(2*math.pi*frame/12)*(1 if part=='leg_l' else -1)
   e['rotation']={'origin':pivots[part],'axis':'x','angle':round(angle,6),'rescale':False}
  elements.append(e)
 return {'credit':'Original frost Yeti inspired by supplied visual reference.',
         'textures':{name:'yetiboss:boss/'+name for name in COLORS},'elements':elements,
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
