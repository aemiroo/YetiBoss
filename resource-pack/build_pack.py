"""CosmeticPets Baby Yeti reused at boss scale."""
import hashlib,json,math,pathlib,struct,zlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
from pet_model import winter_model,yeti_walk_model,limb
COLORS={'coal': (35, 30, 32, 255), 'yeti_blue': (109, 204, 229, 255), 'yeti_cream': (235, 235, 216, 255), 'yeti_face': (117, 153, 168, 255), 'yeti_fur_light': (249, 249, 237, 255), 'yeti_fur_shadow': (204, 209, 185, 255), 'yeti_horn': (155, 162, 132, 255), 'yeti_nose': (74, 105, 119, 255), 'yeti_smile': (48, 78, 90, 255)}
def png(color):
 def chunk(kind,data): return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 raw=b''.join(b'\0'+bytes(color)*16 for _ in range(16))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',16,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def model(frame=None,attack=None):
 # Use the actual pet geometry/colors. The server scales it to boss size.
 if attack is not None:
  result=winter_model('yeti',articulated=True)
  for element in result['elements']:
   part=limb('yeti',element['from'])
   if part is None:continue
   kind,side=part
   pivot=([2.5 if side==0 else 13.5,9,8.5] if kind=='arm'
          else [6 if side==0 else 10,3,7.5])
   angle=-40*math.sin(math.pi*attack/7) if kind=='arm' else 0
   element['rotation']={'origin':pivot,'axis':'x','angle':round(angle,6),'rescale':False}
 else:
  result=winter_model('yeti') if frame is None else yeti_walk_model(frame)
 result['textures']={name:'yetiboss:boss/'+name for name in result['textures']}
 result['credit']='CosmeticPets Baby Yeti geometry, enlarged by the boss display.'
 return result
MODELS=('giant_yeti',)+tuple('giant_yeti_walk_'+str(i) for i in range(12))+tuple('giant_yeti_attack_'+str(i) for i in range(8))
def files():
 result={'pack.mcmeta':json.dumps({'pack':{'description':'YetiBoss - Giant Yeti','min_format':[97,1],'max_format':[97,1]}}).encode(),
         'LICENSE.txt':b'Boss pack GPL-3.0; reused CosmeticPets models/textures MIT. See LICENSE-CosmeticPets.txt.\n'}
 result['LICENSE-CosmeticPets.txt']=(ROOT/'resource-pack/LICENSE-CosmeticPets.txt').read_bytes()
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
