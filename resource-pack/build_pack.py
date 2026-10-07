"""Original frost Yeti boss resource pack."""
import base64,hashlib,json,math,pathlib,struct,zlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
from boss_model import model,COLORS,texture_color
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
MODELS=('giant_yeti',)+tuple('giant_yeti_walk_'+str(i) for i in range(12))+tuple('giant_yeti_attack_'+str(i) for i in range(8))+tuple('giant_yeti_'+kind+'_'+str(i) for kind in ('swipe','throw','roar') for i in range(8))
def files():
 result={'pack.mcmeta':json.dumps({'pack':{'description':'YetiBoss - Giant Yeti','min_format':[97,1],'max_format':[97,1]}}).encode(),
         'LICENSE.txt':b'Original YetiBoss model and textures: GPL-3.0. Audio clips supplied by the server owner; original audio rights remain with their respective creators.\n'}
 for name in MODELS:
  if name=='giant_yeti':m=model()
  else:
   kind=name.split('_')[-2];index=int(name.rsplit('_',1)[1])
   m=model(frame=index) if kind=='walk' else model(attack=index,kind='slam' if kind=='attack' else kind)
  result['assets/yetiboss/models/boss/'+name+'.json']=json.dumps(m).encode()
  result['assets/yetiboss/items/'+name+'.json']=json.dumps({'model':{'type':'minecraft:model','model':'yetiboss:boss/'+name}}).encode()
 for name,color in COLORS.items():result['assets/yetiboss/textures/boss/'+name+'.png']=png(name)
 result['assets/minecraft/atlases/items.json']=json.dumps({'sources':[{'type':'minecraft:single','resource':'yetiboss:boss/'+name,'sprite':'yetiboss:boss/'+name} for name in COLORS]}).encode()
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
