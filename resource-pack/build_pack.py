"""Original frost Yeti boss resource pack."""
import base64,hashlib,json,math,pathlib,struct,zlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
from gear_model import GEAR_MODELS, MATERIALS, model as gear_model, texture as gear_texture, item_definition
from boss_model import model,mother_model,COLORS,texture_color
def png(name):
 def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 rows=[]
 for y in range(16):
  row=bytearray()
  for x in range(16):
   row.extend(list(texture_color(name,x,15-y))+[255])
  rows.append(b'\0'+bytes(row))
 raw=b''.join(rows)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
SOUNDS=('idle','angry','spawn','death','hurt_1','hurt_2','grab_slam')
FATHER_MODELS=('giant_yeti',)+tuple('giant_yeti_walk_'+str(i) for i in range(24))+tuple('giant_yeti_attack_'+str(i) for i in range(8))+tuple('giant_yeti_'+kind+'_'+str(i) for kind in ('swipe','throw','roar') for i in range(8))
MODELS=FATHER_MODELS+tuple(name.replace('giant_yeti','mother_yeti') for name in FATHER_MODELS if '_walk_' not in name or int(name.rsplit('_',1)[1])<12)
def files():
 result={'pack.mcmeta':json.dumps({'pack':{'description':'YetiBoss - Father and Mother Yeti','min_format':[97,1],'max_format':[97,1]}}).encode(),
         'LICENSE.txt':b'Original YetiBoss model and textures: GPL-3.0. Audio clips supplied by the server owner; original audio rights remain with their respective creators.\n'}
 for name in MODELS:
  make=mother_model if name.startswith('mother_yeti') else model
  if name in ('giant_yeti','mother_yeti'):m=make()
  else:
   kind=name.split('_')[-2];index=int(name.rsplit('_',1)[1])
   m=make(frame=index) if kind=='walk' else make(attack=index,kind='slam' if kind=='attack' else kind)
  result['assets/yetiboss/models/boss/'+name+'.json']=json.dumps(m).encode()
  result['assets/yetiboss/items/'+name+'.json']=json.dumps({'model':{'type':'minecraft:model','model':'yetiboss:boss/'+name}}).encode()
 result['GEAR-SOURCES.txt']=(ROOT/'resource-pack/imported/SOURCES.md').read_bytes()
 for name in GEAR_MODELS:
  result['assets/yetiboss/models/gear/'+name+'.json']=json.dumps(gear_model(name)).encode()
  if '_pull_' not in name:result['assets/yetiboss/items/'+name+'.json']=json.dumps(item_definition(name)).encode()
 for name in MATERIALS:result['assets/yetiboss/textures/gear/'+name+'.png']=gear_texture(name)
 for name,color in COLORS.items():result['assets/yetiboss/textures/boss/'+name+'.png']=png(name)
 result['assets/minecraft/atlases/items.json']=json.dumps({'sources':[{'type':'minecraft:single','resource':'yetiboss:boss/'+name,'sprite':'yetiboss:boss/'+name} for name in COLORS]+[{'type':'minecraft:single','resource':'yetiboss:gear/'+name,'sprite':'yetiboss:gear/'+name} for name in MATERIALS]}).encode()
 result['assets/yetiboss/sounds.json']=json.dumps({name:{'sounds':[{'name':'yetiboss:'+name,'stream':False}]} for name in SOUNDS}).encode()
 for name in SOUNDS:
  result['assets/yetiboss/sounds/'+name+'.ogg']=base64.b64decode((ROOT/'resource-pack/sounds'/ (name+'.ogg.b64')).read_text())
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
