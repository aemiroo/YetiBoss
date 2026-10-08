"""Original low-poly frost gear, with hand and inventory transforms."""
import math,struct,zlib
MATERIALS={'gear_ice':(118,173,200),'gear_edge':(221,242,249),'gear_core':(35,83,120),
 'gear_steel':(35,43,55),'gear_grip':(70,49,38),'gear_silver':(153,173,186),'gear_string':(212,223,230)}
def color(name,x,y):
 base=MATERIALS[name]
 grain=((x*13+y*7+x*y*3)%11)-5
 if name=='gear_ice':
  crack=3+(y//2)%4;branch=11-(y//3)%4
  if x in (crack,branch):return (42,96,130)
  if x in (crack+1,branch+1) or (x*7+y*11)%29==0:return (186,229,242)
  rim=17 if min(x,y,15-x,15-y)<2 else 0
  return tuple(min(255,c+grain+rim) for c in base)
 if name=='gear_edge':
  shade=-24 if x in (0,15) else 5 if (x+y)%9==0 else grain
 elif name=='gear_steel':
  shade=45 if x in (0,15) or y in (0,15) else 11 if y%4==0 else grain
 elif name=='gear_grip':
  if x in (2,13) and y%4==1:return (151,125,91)
  shade=17 if y%4 in (0,1) else -10
 elif name=='gear_core':
  if (x in (6,9) and 3<=y<=12) or (y in (3,7,12) and 6<=x<=9):return (99,212,237)
  shade=grain
 elif name=='gear_silver':shade=23 if x<3 else -20 if x>12 else grain
 else:shade=grain//2
 return tuple(max(0,min(255,c+shade)) for c in base)
def grip_point(name):
 if name=='frostfang':return (8,2.85,8)
 if name=='frostpickaxe':return (8,3,8)
 return (8.4,8,8)
def hand_pose(name,rotation,scale,target,left=False):
 # Anchor the physical grip to the vanilla holder's palm, before parent transforms.
 x,y,z=(v-8 for v in grip_point(name))
 rx,ry,rz=rotation
 if left:
  ry,rz=-ry,-rz
  target=(-target[0],target[1],target[2])
 for axis,degrees in (('z',rz),('y',ry),('x',rx)):
  c=math.cos(math.radians(degrees));s=math.sin(math.radians(degrees))
  if axis=='z':x,y=x*c-y*s,x*s+y*c
  elif axis=='y':x,z=x*c+z*s,-x*s+z*c
  else:y,z=y*c-z*s,y*s+z*c
 translation=[round(t-v*scale,6) for t,v in zip(target,(x,y,z))]
 if left:translation[0]=-translation[0]
 return {'rotation':rotation,'translation':translation,'scale':[scale]*3}
GEAR_MODELS=('frostfang','frostbow','frostbow_pull_0','frostbow_pull_1','frostbow_pull_2','frostpickaxe')
GEAR_ITEMS={'frostfang':'minecraft:netherite_sword','frostbow':'minecraft:bow','frostpickaxe':'minecraft:netherite_pickaxe'}
def texture(name):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 def pixel(x,y):
  return bytes(color(name,x,y))+b'\xff'
 raw=b''.join(b'\0'+b''.join(pixel(x,y) for x in range(16)) for y in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def model(name):
 es=[]
 def box(a,b,mat):
  es.append({'from':a,'to':b,'faces':{f:{'uv':[0,0,16,16],'texture':'#'+mat} for f in ('north','south','east','west','up','down')}})
 if name=='frostfang':
  box([7.3,1,7.3],[8.7,4.7,8.7],'gear_grip')
  box([7.05,.5,7.05],[8.95,1.25,8.95],'gear_steel')
  box([5,4.5,7],[11,5.4,9],'gear_steel')
  box([4.3,5,7.15],[5.4,6.2,8.85],'gear_ice')
  box([10.6,5,7.15],[11.7,6.2,8.85],'gear_ice')
  box([6.6,5.4,7.4],[9.4,12.8,8.6],'gear_ice')
  box([6.05,6,7.55],[6.6,8.6,8.45],'gear_edge')
  box([9.4,9.2,7.55],[9.95,11.7,8.45],'gear_edge')
  box([7,12.8,7.4],[9,14.2,8.6],'gear_edge')
  box([7.4,14.2,7.55],[8.6,15.2,8.45],'gear_edge')
  box([7.75,15.2,7.7],[8.25,16,8.3],'gear_edge')
  box([7.7,6,7.22],[8.3,12.6,7.4],'gear_core')
 elif name=='frostpickaxe':
  box([7.25,.7,7.25],[8.75,10.3,8.75],'gear_grip')
  box([7.05,.3,7.05],[8.95,1,8.95],'gear_steel')
  box([6.75,9.4,6.9],[9.25,12.3,9.1],'gear_steel')
  box([3,10.5,7.2],[6.75,12.1,8.8],'gear_ice')
  box([9.25,10.5,7.2],[13,12.1,8.8],'gear_ice')
  box([1.8,9.3,7.35],[3.3,11.5,8.65],'gear_edge')
  box([12.7,9.3,7.35],[14.2,11.5,8.65],'gear_edge')
  box([1.1,8,7.55],[2.2,9.8,8.45],'gear_core')
  box([13.8,8,7.55],[14.9,9.8,8.45],'gear_core')
  box([7.35,10,6.65],[8.65,11.7,6.9],'gear_edge')
 else:
  stage=-1 if name=='frostbow' else int(name.rsplit('_',1)[1])
  shift=max(0,stage+1)*.3
  box([7.6,6.2,7.25],[9.2,9.8,8.75],'gear_grip')
  for a,b in (([7.8,3.5,7.3],[9.1,6.2,8.7]),([7.8,9.8,7.3],[9.1,12.5,8.7])):box(a,b,'gear_steel')
  box([6.5+shift,1.8,7.25],[8.6+shift,3.5,8.75],'gear_ice')
  box([6.5+shift,12.5,7.25],[8.6+shift,14.2,8.75],'gear_ice')
  box([4.7+shift,.8,7.35],[6.8+shift,1.8,8.65],'gear_edge')
  box([4.7+shift,14.2,7.35],[6.8+shift,15.2,8.65],'gear_edge')
  # Thin, stepped string bends toward the hand as the bow is drawn.
  middle=4.9-max(0,stage+1)*1.1
  for i in range(14):
   y=1+i;fraction=abs((y+.5)-8)/7
   x=middle+(4.9+shift-middle)*fraction
   box([x,y,7.87],[x+.14,y+1,8.13],'gear_string')
  if stage>=0:
   box([middle,7.85,7.75],[13.7,8.15,8.05],'gear_silver')
   box([13.7,7.55,7.6],[14.8,8.45,8.2],'gear_ice')
 display={'gui':{'rotation':[15,-20,-30],'translation':[0,0,0],'scale':[.85,.85,.85]},
 'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
 'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[.8,.8,.8]}}
 # The palm anchors are measured in item-model units; left-hand mirroring is applied by Minecraft.
 bow=name.startswith('frostbow')
 right=[-90,0,0] if bow else [0,-90,-90]
 left=[-90,0,0] if bow else [0,90,90]
 display['thirdperson_righthand']=hand_pose(name,right,.85,(0,-2,1))
 display['thirdperson_lefthand']=hand_pose(name,left,.85,(0,-2,1),True)
 display['firstperson_righthand']=hand_pose(name,[0,-90,0],.68,(1.13,-1.3,-.5))
 display['firstperson_lefthand']=hand_pose(name,[0,90,0],.68,(1.13,-1.3,-.5),True)
 return {'textures':{n:'yetiboss:gear/'+n for n in MATERIALS},'elements':es,'display':display}
def item_definition(name):
 def reference(n):return {'type':'minecraft:model','model':'yetiboss:gear/'+n}
 if name!='frostbow':return {'model':reference(name)}
 return {'model':{'type':'minecraft:condition','property':'minecraft:using_item',
  'on_false':reference('frostbow'),'on_true':{'type':'minecraft:range_dispatch',
   'property':'minecraft:use_duration','scale':.05,
   'fallback':reference('frostbow_pull_0'),
   'entries':[{'threshold':.65,'model':reference('frostbow_pull_1')},
              {'threshold':.9,'model':reference('frostbow_pull_2')}]}}}


def icon(name):
 """Transparent inventory sprite from the exact front silhouette."""
 m=model(name);pixels=[(0,0,0,0)]*256
 for e in sorted(m['elements'],key=lambda e:e['from'][2],reverse=True):
  a,b=e['from'],e['to'];mat=e['faces']['north']['texture'][1:]
  for y in range(16):
   for x in range(16):
    if a[0]<x+1 and x<b[0] and a[1]<16-y and 15-y<b[1]:pixels[y*16+x]=color(mat,x,15-y)+(255,)
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+b''.join(bytes(p) for p in pixels[y*16:(y+1)*16]) for y in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
