import json, unittest
from build_pack import files,model,MODELS,COLORS
from build_bedrock import files as bedrock_files,mappings,display_mappings
class BossPackTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.java=files();cls.bedrock=bedrock_files()
 def test_models_and_textures_resolve(self):
  for name in MODELS:
   item=json.loads(self.java['assets/yetiboss/items/'+name+'.json'])
   self.assertEqual('yetiboss:boss/'+name,item['model']['model'])
   m=json.loads(self.java['assets/yetiboss/models/boss/'+name+'.json'])
   for texture in m['textures'].values():
    self.assertIn('assets/'+texture.replace(':','/textures/')+'.png',self.java)
   for element in m['elements']:
    self.assertTrue(element['faces'])
    for bound in ('from','to'):self.assertTrue(all(0<=v<=16 for v in element[bound]))
    if 'rotation' in element:self.assertIn(element['rotation']['angle'],(-45,-22.5,0,22.5,45))
 def test_approved_shape_and_scream_teeth(self):
  rest=model();roar=model(attack=3,kind='roar')
  self.assertEqual(0,min(e['from'][1] for e in rest['elements']))
  self.assertTrue(any(e['faces']['north']['texture']=='#horn' for e in rest['elements']))
  self.assertFalse(any(e['faces']['north']['texture']=='#tooth' for e in rest['elements']))
  teeth=[e for e in roar['elements'] if e['faces']['north']['texture']=='#tooth']
  self.assertGreater(len(teeth),6)
  self.assertTrue(all(e['to'][2]<=3.65 for e in teeth))
 def test_walk_moves_both_arms_together_and_legs_alternate(self):
  rest=model();walk=model(frame=3)
  for start in ([1.3,1.2,5.8],[12,1.2,5.8]):
   i=next(i for i,e in enumerate(rest['elements']) if e['from']==start)
   self.assertAlmostEqual(.5,walk['elements'][i]['from'][2]-rest['elements'][i]['from'][2])
  for start,sign in (([4.8,1,6.6],1),([8.8,1,6.6],-1)):
   i=next(i for i,e in enumerate(rest['elements']) if e['from']==start)
   self.assertAlmostEqual(sign*.6,walk['elements'][i]['from'][2]-rest['elements'][i]['from'][2])
 def test_attack_poses_raise_both_arms(self):
  rotations=[e['rotation'] for e in model(attack=3)['elements'] if 'rotation' in e]
  for pivot in ([3.5,9,8],[12.5,9,8]):
   self.assertTrue(any(r['origin']==pivot and r['axis']=='x' and r['angle']==-45 for r in rotations))
 def test_custom_sounds_are_in_both_packs(self):
  for name in ('idle','angry'):
   data=self.java['assets/yetiboss/sounds/'+name+'.ogg']
   self.assertTrue(data.startswith(b'OggS'))
   self.assertEqual(data,self.bedrock['sounds/yetiboss/'+name+'.ogg'])
 def test_bedrock_contains_all_poses_and_preserves_pivots(self):
  self.assertEqual(len(MODELS),len(mappings()['items']['minecraft:paper']))
  for name in MODELS:
   self.assertIn('attachables/'+name+'.json',self.bedrock)
   self.assertIn('yetiboss:'+name,display_mappings())
   m=json.loads(self.java['assets/yetiboss/models/boss/'+name+'.json'])
   geo=json.loads(self.bedrock['models/entity/'+name+'.geo.json'])
   cubes=geo['minecraft:geometry'][0]['bones'][0]['cubes']
   self.assertEqual(len(m['elements']),len(cubes))
   for e,c in zip(m['elements'],cubes):
    if 'rotation' in e:
     x,y,z=e['rotation']['origin']
     self.assertEqual([8-x,y+8,z-8],c['pivot'])
     r=e['rotation'];expected=[0,0,0];expected['xyz'.index(r['axis'])]=r['angle']*(-1 if r['axis']=='x' else 1)
     self.assertEqual(expected,c['rotation'])
 def test_pack_namespaces_do_not_replace_pet_models(self):
  self.assertFalse(any('assets/cosmeticpets/' in p for p in self.java))
  self.assertFalse(any(p.startswith('assets/minecraft/models/') for p in self.java))

 def test_textured_fur_is_preserved_in_bedrock_atlas(self):
  import zlib,struct
  def raw(png):
   pos=8
   while pos<len(png):
    n=struct.unpack('>I',png[pos:pos+4])[0]
    if png[pos+4:pos+8]==b'IDAT':return zlib.decompress(png[pos+8:pos+8+n])
    pos+=n+12
  m=model();names=list(m['textures']);tile=names.index('fur')
  java=raw(self.java['assets/yetiboss/textures/boss/fur.png'])
  bedrock=raw(self.bedrock['textures/yetiboss/giant_yeti.png'])
  width=len(names)*64+1
  for y in range(16):
   self.assertEqual(java[y*65+1:y*65+65],bedrock[y*width+1+tile*64:y*width+1+(tile+1)*64])
  self.assertGreater(len(set(java[1:65])),4)

 def test_roar_mouth_is_in_front_of_chest_and_mesh_is_compact(self):
  m=model(attack=3,kind='roar');self.assertLess(len(m['elements']),80)
  cavity=[e for e in m['elements'] if e['faces']['north']['texture']=='#scream']
  self.assertLess(max(e['to'][2] for e in cavity),6)
