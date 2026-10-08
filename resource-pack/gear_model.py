"""Original low-poly frost gear, with hand and inventory transforms."""
import math,struct,zlib
MATERIALS={'gear_ice':(118,173,200),'gear_edge':(221,242,249),'gear_core':(35,83,120),
 'gear_steel':(35,43,55),'gear_grip':(70,49,38),'gear_silver':(153,173,186),'gear_string':(212,223,230),'gear_gem':(58,174,229),'gear_rune':(22,47,68),'gear_binding':(108,77,53)}
def color(name,x,y):
 base=MATERIALS[name]
 grain=((x*13+y*7+x*y*3)%11)-5
 if name=='gear_gem':
  if x<4 and y>10:return (228,251,255)
  if x+y>20:return (24,105,167)
  if x<8:return (116,224,251)
  return (51,170,221)
 if name=='gear_rune':
  if (x in (4,11) and 3<=y<=12) or (x+y in (10,17) and 3<=x<=12):return (111,230,250)
  return base
 if name=='gear_binding':
  return tuple(max(0,min(255,c+ (16 if y<4 else -12 if y>11 else grain))) for c in base)
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
 def box(a,b,mat,rotation=None):
  e={'from':list(a),'to':list(b),'faces':{f:{'uv':[0,0,16,16],'texture':'#'+mat} for f in ('north','south','east','west','up','down')}}
  if rotation:e['rotation']=rotation
  es.append(e);return e
 def square(x,y,size,z,mat):
  return box([x-size,y-size,z],[x+size,y+size,z+.24],mat,
   {'origin':[x,y,z+.12],'axis':'z','angle':45,'rescale':False})
 def jewel(x,y,size=.45,z=6.4):
  square(x,y,size+.16,z+.16,'gear_steel')
  square(x,y,size,z,'gear_gem')
  square(x,y,size*.32,z-.08,'gear_edge')
 def ring(x,y,width=1.9,z=7):box([x-width/2,y,z],[x+width/2,y+.34,16-z],'gear_silver')
 def wraps(x,lo,hi):
  for i in range(int((hi-lo)/.5)):
   y=lo+i*.5
   box([x-.87,y,7.03],[x+.87,y+.14,8.97],'gear_binding')
 def plate(x,y,width=1.0,height=1,z=6.85):
  box([x-width/2-.12,y-.1,z+.08],[x+width/2+.12,y+height+.1,z+.3],'gear_steel')
  box([x-width/2,y,z],[x+width/2,y+height,z+.08],'gear_rune')
 if name=='frostfang':
  # Leather hilt, forged collars, and faceted pommel.
  box([7.22,1.1,7.22],[8.78,4.45,8.78],'gear_grip')
  wraps(8,1.25,4.25);ring(8,1.02);ring(8,4.25)
  box([7.05,.45,7.05],[8.95,1.1,8.95],'gear_steel')
  jewel(8,.75,.31,6.65)
  # Curved dark guard with outward ice hooks.
  box([6.4,4.6,6.95],[9.6,5.45,9.05],'gear_steel')
  for right in (False,True):
   def guard(a,b,mat):
    if right:a,b=[16-b[0],a[1],a[2]],[16-a[0],b[1],b[2]]
    box(a,b,mat)
   guard([5.15,4.35,7.05],[6.4,5.15,8.95],'gear_steel')
   guard([4.15,3.85,7.2],[5.15,4.7,8.8],'gear_steel')
   guard([3.8,3.5,7.4],[4.45,5.7,8.6],'gear_ice')
   guard([3.9,5.7,7.55],[4.35,6.25,8.45],'gear_edge')
   guard([4.1,3.1,7.6],[4.4,3.5,8.4],'gear_edge')
   guard([4.65,4.2,6.87],[6.15,4.48,7.05],'gear_silver')
  jewel(8,5.0,.48,6.4)
  # Narrow forged blade, framed by stepped, crystalline cutting edges.
  box([6.7,5.45,7.3],[9.3,13.75,8.7],'gear_steel')
  box([7.1,13.75,7.4],[8.9,14.65,8.6],'gear_steel')
  box([7.5,14.65,7.5],[8.5,15.2,8.5],'gear_ice')
  box([7.75,15.2,7.65],[8.25,15.95,8.35],'gear_edge')
  for y,width,height in ((5.5,1.25,1.8),(7.3,1.1,1.7),(9,1.0,1.7),(10.7,.8,1.6),(12.3,.65,1.45),(13.75,.4,.9)):
   for right in (False,True):
    x=9.3 if right else 6.7-width
    box([x,y,7.34],[x+width,y+height,8.66],'gear_ice')
    edge=x+width-.19 if right else x
    box([edge,y+.1,7.2],[edge+.19,y+height-.08,8.8],'gear_edge')
    if y<12.3:
     tip=x+width+.1 if right else x-.1
     square(tip,y+.48,.24,7.55,'gear_edge')
  for z in (7.05,8.7):
   box([7.38,5.65,z],[8.62,14.1,z+.25],'gear_core')
   for y in (6,7.9,9.8,11.7,13.1):
    box([7.65,y,z+.25 if z>8 else z-.07],[8.35,y+.58,z+.32 if z>8 else z],'gear_rune')
 elif name=='frostpickaxe':
  # Long wrapped haft, silver ferrules and a jewel on the socket.
  box([7.2,.8,7.2],[8.8,13.1,8.8],'gear_grip')
  wraps(8,1.3,11.9)
  for y in (1,5.25,9.7,12.3):ring(8,y,2.0,6.95)
  box([7,.4,7],[9,1,9],'gear_steel');jewel(8,.8,.32,6.55)
  plate(8,6.7,.65,1.05)
  box([6.55,12.1,6.8],[9.45,14.45,9.2],'gear_steel')
  box([6.9,14.45,7],[9.1,15.1,9],'gear_silver')
  for right in (False,True):
   for x0,x1,y0,y1 in ((5.2,6.55,12.8,14.0),(3.8,5.2,12.3,13.7),(2.5,3.8,11.6,13.1),(1.35,2.5,10.6,12.15),(.65,1.35,9.55,11.0)):
    if right:x0,x1=16-x1,16-x0
    box([x0,y0,7.12],[x1,y1,8.88],'gear_steel')
    box([x0+.08,y0-.27,6.9],[x1-.08,y0+.3,9.1],'gear_ice')
    box([x0+.12,y0-.42,7.05],[x1-.12,y0-.27,8.95],'gear_edge')
    box([x0+.1,y1-.21,7.28],[x1-.1,y1,8.72],'gear_silver')
   square(15.1 if right else .9,9.35,.32,7.6,'gear_edge')
   plate(11.05 if right else 4.95,12.65,.68,.6,6.72)
  jewel(8,13.3,.65,6.3)
 else:
  stage=-1 if name=='frostbow' else int(name.rsplit('_',1)[1])
  # The central wrapped grip never moves during the draw.
  box([7.6,6.2,7.25],[9.2,9.8,8.75],'gear_grip')
  wraps(8.4,6.3,9.5);ring(8.4,6.0,2.1,7);ring(8.4,9.65,2.1,7)
  upper=((6.7,8.6,9.8,10.9),(5.6,7.3,10.9,12.2),(6.05,7.75,12.2,13.2),
         (7.35,9.1,13.2,14.0),(8.7,10.5,14.0,14.6),(10,12.2,14.6,15.2))
  for lower in (False,True):
   for i,(x0,x1,y0,y1) in enumerate(upper):
    bend=max(0,stage+1)*.065*(5-i);x0+=bend;x1+=bend
    if lower:y0,y1=16-y1,16-y0
    box([x0,y0,7.22],[x1,y1,8.78],'gear_steel')
    box([x0-.28,y0+.05,7.05],[x0+.2,y1-.05,8.95],'gear_ice')
    box([x0-.4,y0+.13,7.2],[x0-.28,y1-.13,8.8],'gear_edge')
    if i in (0,3):plate((x0+x1)/2,y0+.2,.65,max(.2,y1-y0-.4),6.95)
   jewel(8.4,5.8 if lower else 10.2,.38,6.5)
   jewel(6.5,4.1 if lower else 11.9,.28,6.65)
   for j,(x,y,size) in enumerate(((5.25,11.1,.46),(4.9,11.9,.38),(5.15,12.6,.28))):
    if lower:y=16-y
    square(x,y,size,7.4+j*.13,'gear_ice')
    square(x-.1,y+.05,size*.55,7.12+j*.11,'gear_edge')
   square(12.0,1.0 if lower else 15.0,.43,7.4,'gear_ice')
  # Connected voxel string stretches back, with a properly directed nocked arrow.
  end=12.15;middle=end+max(0,stage+1)*.55
  for i in range(28):
   y0=.85+i*.51;y1=y0+.51
   def string_x(y):return middle-(middle-end)*abs(y-8)/7.15
   x0,x1=string_x(y0),string_x(y1)
   box([min(x0,x1)-.045,y0,7.95],[max(x0,x1)+.045,y1,8.05],'gear_string')
  if stage>=0:
   box([1.25,7.9,7.83],[middle,8.1,8.03],'gear_silver')
   square(1.2,8,.32,7.7,'gear_ice')
   for y in (7.62,8.1):box([middle-.8,y,7.82],[middle-.2,y+.28,8.04],'gear_edge')
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
 """64px transparent front projection of the exact textured voxel model."""
 m=model(name);size=64;pixels=[(0,0,0,0)]*(size*size)
 for e in sorted(m['elements'],key=lambda e:e['from'][2],reverse=True):
  a,b=e['from'],e['to'];mat=e['faces']['north']['texture'][1:]
  for y in range(size):
   for x in range(size):
    px,py=(x+.5)*16/size,16-(y+.5)*16/size
    if 'rotation' in e:
     r=e['rotation'];ox,oy,_=r['origin'];angle=-math.radians(r['angle'])
     px,py=ox+(px-ox)*math.cos(angle)-(py-oy)*math.sin(angle),oy+(px-ox)*math.sin(angle)+(py-oy)*math.cos(angle)
    if a[0]<=px<b[0] and a[1]<=py<b[1]:
     u=min(15,int((px-a[0])/(b[0]-a[0])*16));v=min(15,int((py-a[1])/(b[1]-a[1])*16))
     pixels[y*size+x]=color(mat,u,v)+(255,)
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+b''.join(bytes(p) for p in pixels[y*size:(y+1)*size]) for y in range(size))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
