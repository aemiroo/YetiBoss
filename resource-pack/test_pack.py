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
 def test_reference_shape_has_fur_red_eyes_and_deep_mouth(self):
  m=model()
  self.assertEqual(0,min(e['from'][1] for e in m['elements']))
  self.assertGreaterEqual(max(e['to'][1] for e in m['elements']),15.9)
  for name in ('fur','frost','face','tooth','mouth','eye'):
   self.assertTrue(any(f['texture']=='#'+name for e in m['elements'] for f in e['faces'].values()))
  mouth=[e for e in m['elements'] if any(f['texture']=='#mouth' for f in e['faces'].values())]
  teeth=[e for e in m['elements'] if any(f['texture']=='#tooth' for f in e['faces'].values())]
  self.assertGreater(max(e['from'][2] for e in mouth),min(e['from'][2] for e in teeth)+2)
 def test_walk_moves_both_arms_together_and_legs_alternate(self):
  rest=model();walk=model(frame=3)
  # Identify corresponding pieces by order; the pose changes their positions.
  left=next(i for i,e in enumerate(rest['elements']) if e['from']==[.8,2.5,4.9])
  right=next(i for i,e in enumerate(rest['elements']) if e['from']==[12.3,2.5,4.9])
  self.assertAlmostEqual(.5,walk['elements'][left]['from'][2]-rest['elements'][left]['from'][2])
  self.assertAlmostEqual(.5,walk['elements'][right]['from'][2]-rest['elements'][right]['from'][2])
  for start,sign in (([5.2,1.1,7],1),([8.5,1.1,7],-1)):
   i=next(i for i,e in enumerate(rest['elements']) if e['from']==start)
   self.assertAlmostEqual(sign*.65,walk['elements'][i]['from'][2]-rest['elements'][i]['from'][2])
 def test_attack_poses_raise_both_arms(self):
  rotations=[e['rotation'] for e in model(attack=3)['elements'] if 'rotation' in e]
  for pivot in ([3.5,10.5,8],[12.5,10.5,8]):
   self.assertTrue(any(r['origin']==pivot and r['axis']=='x' and r['angle']==-45 for r in rotations))
 def test_bedrock_contains_all_poses_and_preserves_pivots(self):
  self.assertEqual(21,len(mappings()['items']['minecraft:paper']))
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

 def test_open_mouth_is_in_front_of_the_chest_and_mesh_is_compact(self):
  m=model();self.assertLess(len(m['elements']),200)
  cavity=[e for e in m['elements'] if e['faces']['north']['texture']=='#mouth']
  self.assertLess(max(e['to'][2] for e in cavity),6.05)
