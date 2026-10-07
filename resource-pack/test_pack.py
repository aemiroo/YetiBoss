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
 def test_reference_shape_has_tall_horns_blue_extremities_and_open_mouth(self):
  m=model()
  self.assertEqual(0,min(e['from'][1] for e in m['elements']))
  self.assertEqual(16,max(e['to'][1] for e in m['elements']))
  for name in ('horn','frost','face','tooth','mouth','eye'):
   self.assertTrue(any(f['texture']=='#'+name for e in m['elements'] for f in e['faces'].values()))
  horns=[e for e in m['elements'] if any(f['texture'].startswith('#horn') for f in e['faces'].values())]
  self.assertGreaterEqual(max(e['to'][1] for e in horns)-min(e['from'][1] for e in horns),5)
 def test_arms_swing_together_and_legs_alternate(self):
  for frame in range(12):
   m=model(frame=frame)
   rotations={tuple(e['rotation']['origin']):e['rotation']['angle'] for e in m['elements'] if 'rotation' in e}
   self.assertEqual(rotations[(2,9,8.5)],rotations[(14,9,8.5)])
   self.assertAlmostEqual(rotations[(6.5,5,8.5)],-rotations[(10.5,5,8.5)])
 def test_attack_poses_raise_both_arms(self):
  m=model(attack=3)
  rotations={tuple(e['rotation']['origin']):e['rotation']['angle'] for e in m['elements'] if 'rotation' in e}
  self.assertEqual(rotations[(2,9,8.5)],rotations[(14,9,8.5)])
  self.assertLess(rotations[(2,9,8.5)],-35)
  self.assertEqual(0,rotations[(6.5,5,8.5)])
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
     self.assertEqual([-e['rotation']['angle'],0,0],c['rotation'])
 def test_pack_namespaces_do_not_replace_pet_models(self):
  self.assertFalse(any('assets/cosmeticpets/' in p for p in self.java))
  self.assertFalse(any(p.startswith('assets/minecraft/models/') for p in self.java))
