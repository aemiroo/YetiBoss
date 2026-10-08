"""Original low-poly frost gear, with hand and inventory transforms."""
import struct,zlib
MATERIALS={'gear_ice':(81,199,230),'gear_edge':(202,246,255),'gear_core':(29,119,165),
 'gear_steel':(38,58,77),'gear_grip':(61,78,91),'gear_silver':(151,187,205),'gear_string':(225,242,249)}
GEAR_MODELS=('frostfang','frostbow','frostbow_pull_0','frostbow_pull_1','frostbow_pull_2','frostpickaxe')
GEAR_ITEMS={'frostfang':'minecraft:netherite_sword','frostbow':'minecraft:bow','frostpickaxe':'minecraft:netherite_pickaxe'}
def texture(name):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 def pixel(x,y):
  base=MATERIALS[name];shade=((x//3+y//4)%3-1)*5
  return bytes(max(0,min(255,c+shade)) for c in base)+b'\xff'
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
 'fixed':{'rotation':[0,180,0],'translation':[0,0,0],'scale':[.8,.8,.8]},
 'thirdperson_righthand':{'rotation':[0,-90,55],'translation':[0,4,0],'scale':[.85,.85,.85]},
 'thirdperson_lefthand':{'rotation':[0,90,-55],'translation':[0,4,0],'scale':[.85,.85,.85]},
 'firstperson_righthand':{'rotation':[0,-90,25],'translation':[1.13,3.2,1.13],'scale':[.68,.68,.68]},
 'firstperson_lefthand':{'rotation':[0,90,-25],'translation':[1.13,3.2,1.13],'scale':[.68,.68,.68]}}
 if name.startswith('frostbow'):
  display['firstperson_righthand']={'rotation':[0,-90,25],'translation':[1.13,3.2,1.13],'scale':[.68,.68,.68]}
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
    if a[0]<x+1 and x<b[0] and a[1]<16-y and 15-y<b[1]:pixels[y*16+x]=MATERIALS[mat]+(255,)
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+b''.join(bytes(p) for p in pixels[y*16:(y+1)*16]) for y in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
