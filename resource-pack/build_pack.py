"""Original frost Yeti boss resource pack."""
import hashlib,json,math,pathlib,struct,zlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
from boss_model import model,COLORS
def png(color):
 def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+bytes(color)*16 for _ in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
MODELS=('giant_yeti',)+tuple('giant_yeti_walk_'+str(i) for i in range(12))+tuple('giant_yeti_attack_'+str(i) for i in range(8))
def files():
 result={'pack.mcmeta':json.dumps({'pack':{'description':'YetiBoss - Giant Yeti','min_format':[97,1],'max_format':[97,1]}}).encode(),
         'LICENSE.txt':b'Original YetiBoss model and textures: GPL-3.0. No extracted third-party assets.\n'}
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
