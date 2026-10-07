"""Original Minecraft-style Giant Yeti inspired by the supplied visual reference."""
import hashlib,json,math,pathlib,struct,zlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
COLORS={
 'fur':(231,236,232,255),'fur_shadow':(182,201,207,255),'fur_light':(250,252,245,255),
 'skin':(85,111,121,255),'skin_shadow':(58,78,89,255),'mouth':(49,27,37,255),
 'tongue':(144,65,75,255),'tooth':(242,235,202,255),'eye':(248,99,80,255),
 'ice':(121,208,239,255),'ice_light':(184,242,252,255),'claw':(102,142,157,255)}
def png(color):
 def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+bytes(color)*16 for _ in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def model(frame=None,attack=None):
 cells={}
 def box(a,b,material,part='body'):
  for x in range(a[0],b[0]):
   for y in range(a[1],b[1]):
    for z in range(a[2],b[2]):cells[x,y,z]=(material,part)
 def ball(c,r,material,part='body'):
  for x in range(32):
   for y in range(32):
    for z in range(32):
     if sum(((v+.5-a)/b)**2 for v,a,b in zip((x,y,z),c,r))<=1:cells[x,y,z]=(material,part)
 # Heavy torso, hulking shoulders, long arms and smaller thick feet.
 ball((16,14,18),(8,10,6),'fur')
 box((10,3,14),(15,10,23),'fur','leg_l')
 box((17,3,14),(22,10,23),'fur','leg_r')
 box((9,0,11),(15,4,23),'fur_shadow','leg_l')
 box((17,0,11),(23,4,23),'fur_shadow','leg_r')
 for side,cx in (('l',5),('r',27)):
  ball((cx,19,18),(5,6,5),'fur','arm_'+side)
  box((cx-3,6,14),(cx+3,21,22),'fur','arm_'+side)
  box((cx-3,4,12),(cx+3,8,21),'skin','arm_'+side)
  for x in (cx-3,cx-1,cx+1):box((x,4,11),(x+1,6,13),'claw','arm_'+side)
 # Head set low in a shaggy shoulder mane.
 ball((16,25,14),(6,6,5),'fur')
 box((12,22,8),(20,27,11),'skin')
 box((11,26,8),(15,28,10),'skin_shadow')
 box((17,26,8),(21,28,10),'skin_shadow')
 box((12,25,7),(14,26,9),'eye')
 box((18,25,7),(20,26,9),'eye')
 box((14,23,7),(18,25,10),'skin_shadow')
 box((12,19,7),(20,23,10),'mouth')
 box((14,19,7),(18,20,8),'tongue')
 for x in (12,14,17,19):box((x,22,6),(x+1,23,8),'tooth')
 for x in (13,16,18):box((x,19,6),(x+1,20,8),'tooth')
 # Long tusks outside the mouth.
 for x in (10,20):
  box((x,19,6),(x+2,25,8),'tooth')
  box((x,25,6),(x+1,27,7),'tooth')
 # Pointed mane, beard and wrist tufts use actual stepped geometry.
 for x,y in ((8,23),(10,21),(12,18),(14,17),(17,17),(19,18),(21,21),(23,23)):
  box((x,y,9),(x+2,y+4,12),'fur_light')
  box((x,y-2,10),(x+1,y,12),'fur_shadow')
 for side,cx in (('l',5),('r',27)):
  for dx in (-3,0,2):
   box((cx+dx,8,22),(cx+dx+2,14,24),'fur_light','arm_'+side)
   box((cx+dx,6,22),(cx+dx+1,8,23),'fur_shadow','arm_'+side)
 # Icy crystalline spikes rise from both shoulders and forearms.
 for side,coords in (('l',((2,22,18),(5,24,20),(8,23,19))),
                     ('r',((29,22,18),(26,24,20),(23,23,19)))):
  for x,y,z in coords:
   box((x-1,y,z-1),(x+2,y+3,z+2),'ice','arm_'+side)
   box((x,y+3,z),(x+1,y+6,z+1),'ice_light','arm_'+side)
 for (x,y,z),(material,part) in list(cells.items()):
  if material=='fur':
   value=(x*13+y*3+z*7)%19
   cells[x,y,z]=('fur_shadow' if value<3 else 'fur_light' if value==7 else material,part)
 directions={'west':(-1,0,0),'east':(1,0,0),'down':(0,-1,0),'up':(0,1,0),'north':(0,0,-1),'south':(0,0,1)}
 parts={'leg_l':([12,9,18],1),'leg_r':([20,9,18],-1),
        'arm_l':([5,21,18],1),'arm_r':([27,21,18],1)}
 elements=[]
 for (x,y,z),(material,part) in sorted(cells.items()):
  faces={}
  for face,(dx,dy,dz) in directions.items():
   neighbor=cells.get((x+dx,y+dy,z+dz))
   if neighbor is None or neighbor[1]!=part:faces[face]={'uv':[0,0,16,16],'texture':'#'+material}
  if not faces:continue
  element={'from':[x/2,y/2,z/2],'to':[(x+1)/2,(y+1)/2,(z+1)/2],'faces':faces}
  if part in parts and (frame is not None or attack is not None):
   pivot,sign=parts[part]
   angle=0
   if attack is not None:
    if part.startswith('arm'):angle=-40*math.sin(math.pi*attack/7)
   elif part.startswith('leg'):angle=25*math.sin(2*math.pi*frame/12)*sign
   else:angle=-18*(1-4*abs((frame/12+.25)%1-.5))
   element['rotation']={'origin':[v/2 for v in pivot],'axis':'x','angle':round(angle,6),'rescale':False}
  elements.append(element)
 return {'credit':'Original Giant Yeti model; no third-party assets copied.',
         'textures':{name:'yetiboss:boss/'+name for name in COLORS},
         'elements':elements,'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
MODELS=('giant_yeti',)+tuple('giant_yeti_walk_'+str(i) for i in range(12))+tuple('giant_yeti_attack_'+str(i) for i in range(8))
def files():
 result={'pack.mcmeta':json.dumps({'pack':{'description':'YetiBoss - Giant Yeti','min_format':[97,1],'max_format':[97,1]}}).encode(),
         'LICENSE.txt':b'Original Giant Yeti models and textures. GPL-3.0, same as YetiBoss repository. No extracted third-party assets.\n'}
 for name in MODELS:
  m=model(attack=int(name.rsplit('_',1)[1])) if '_attack_' in name else model(frame=int(name.rsplit('_',1)[1])) if '_walk_' in name else model()
  result['assets/yetiboss/models/boss/'+name+'.json']=json.dumps(m).encode()
  result['assets/yetiboss/items/'+name+'.json']=json.dumps({'model':{'type':'minecraft:model','model':'yetiboss:boss/'+name}}).encode()
 for name,color in COLORS.items():result['assets/yetiboss/textures/boss/'+name+'.png']=png(color)
 result['assets/minecraft/atlases/items.json']=json.dumps({'sources':[{'type':'minecraft:single','resource':'yetiboss:boss/'+name,'sprite':'yetiboss:boss/'+name} for name in COLORS]}).encode()
 return result
def build():
 output=ROOT/'target/YetiBoss-Pack.zip';output.parent.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
  for name,data in sorted(files().items()):
   info=zipfile.ZipInfo(name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,data)
 digest=hashlib.sha1(output.read_bytes()).hexdigest()
 (output.parent/'yeti-pack.sha1').write_text(digest+'\n')
 (ROOT/'src/main/resources/yeti-pack.sha1').write_text(digest+'\n')
 print('Built',output.name,digest)
if __name__=='__main__':build()
