"""Detailed frost gear with hand and inventory transforms."""
import math,struct,zlib,json,pathlib,base64,copy
_IMPORTED=pathlib.Path(__file__).parent/"imported"
_IMPORTED_TEXTURES=json.loads((_IMPORTED/"textures.json").read_text())
MATERIALS={'gear_ice':(147,190,225),'gear_edge':(221,242,249),'gear_core':(35,83,120),
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
  facet=((x//4)*3+(y//5)*5)%5
  shade=(-22,-8,0,17,36)[facet]+grain//2
  return tuple(max(0,min(255,c+shade)) for c in base)
 if name=='gear_edge':
  shade=-24 if x in (0,15) else 5 if (x+y)%9==0 else grain
 elif name=='gear_steel':
  shade=8 if x in (0,15) or y in (0,15) else grain//2
 elif name=='gear_grip':
  if x in (2,13) and y%4==1:return (151,125,91)
  shade=17 if y%4 in (0,1) else -10
 elif name=='gear_core':
  if (x in (6,9) and 3<=y<=12) or (y in (3,7,12) and 6<=x<=9):return (99,212,237)
  shade=grain
 elif name=='gear_silver':shade=23 if x<3 else -20 if x>12 else grain
 else:shade=grain//2
 return tuple(max(0,min(255,c+shade)) for c in base)
def imported(name):
 base=name.split('_pull_')[0]
 return json.loads((_IMPORTED/(base+'.json')).read_text())
def grip_point(name):return tuple(imported(name)['grip'])
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
 if name in _IMPORTED_TEXTURES:return base64.b64decode(_IMPORTED_TEXTURES[name])
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 def pixel(x,y):
  return bytes(color(name,x,y))+b'\xff'
 raw=b''.join(b'\0'+b''.join(pixel(x,y) for x in range(16)) for y in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def model(name):
 original=imported(name)
 es=copy.deepcopy(original['elements'])
 if '_pull_' in name:
  stage=int(name.rsplit('_',1)[1])+1
  from mesh_preview import rotate
  gx,gy,gz=grip_point(name)
  for label,e in zip(original['nodes'],es):
   if label.startswith('Handle'):continue
   center=sum(e[k][1] for k in ('from','to'))/2
   shift=-.15*stage*min(1,abs(center-gy)/5)
   if label.startswith('Rope'):
    # Draw the nocking point while keeping both string halves connected to tips.
    a,b=e['from'],e['to'];center=[(x+y)/2 for x,y in zip(a,b)];length=b[0]-a[0];r=e.get('rotation',{});o=r.get('origin',[0,0,0])
    points=[]
    for sign in (-1,1):
     p=list(center);p[0]+=sign*length/2
     points.append([t+q for t,q in zip(rotate([q-t for q,t in zip(p,o)],r),o)])
    near=min(range(2),key=lambda i:abs(points[i][1]-gy))
    points[near][0]-=.55*stage;points[1-near][0]-=.15*stage
    v=[y-x for x,y in zip(*points)];length=math.sqrt(sum(q*q for q in v));mid=[(x+y)/2 for x,y in zip(*points)];sizes=[length,b[1]-a[1],b[2]-a[2]]
    e['from']=[x-size/2 for x,size in zip(mid,sizes)];e['to']=[x+size/2 for x,size in zip(mid,sizes)]
    e['rotation']={'origin':mid,'x':0,'y':-math.degrees(math.asin(max(-1,min(1,v[2]/length)))),'z':math.degrees(math.atan2(v[1],v[0]))}
   else:
    for k in ('from','to'):e[k][0]+=shift
    if 'rotation' in e:e['rotation']['origin'][0]+=shift
 display={'gui':{'rotation':[0,0,-45],'translation':[0,0,0],'scale':[.85,.85,.85]},
 'ground':{'rotation':[0,0,0],'translation':[0,3,0],'scale':[.45,.45,.45]},
 'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[.8,.8,.8]}}
 # Upright imported bow -> vanilla diagonal sprite basis: Z=135 degrees.
 # Compose that basis into the vanilla bow display rotations (-40+135=95).
 # The palm anchors are measured in item-model units; left-hand mirroring is applied by Minecraft.
 bow=name.startswith('frostbow')
 right=[-80,260,95] if bow else [0,-90,10]
 left=[-80,-280,-95] if bow else [0,90,-10]
 display['thirdperson_righthand']=hand_pose(name,right,1.5 if name=='frostfang' else 1.15,((-1,-2,4.5) if bow else (0,-2,1)))
 display['thirdperson_lefthand']=hand_pose(name,left,1.5 if name=='frostfang' else 1.15,((-1,-2,4.5) if bow else (0,-2,1)),True)
 # Present the sword blade in the same plane as vanilla handheld swords.
 first_right=[0,-90,25] if name=='frostfang' else ([0,-90,160] if bow else [0,-30,-15])
 first_left=[0,90,-25] if name=='frostfang' else ([0,90,-160] if bow else [0,30,15])
 display['firstperson_righthand']=hand_pose(name,first_right,1.3 if name=='frostfang' else .9,((1.13,3.2,1.13) if bow else (1.13,-1.3,-.5)))
 display['firstperson_lefthand']=hand_pose(name,first_left,1.3 if name=='frostfang' else .9,((1.13,3.2,1.13) if bow else (1.13,-1.3,-.5)),True)
 return {'textures':original['textures'],'elements':es,'display':display}
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
 from mesh_preview import raster
 from png_codec import encode
 m=model(name)
 rgba=raster(m,{k:texture(k) for k in m['textures']},64,64,3.5)
 return encode(64,64,rgba)

MATERIALS.update({name:(255,255,255) for name in _IMPORTED_TEXTURES})
