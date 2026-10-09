import json,unittest,zipfile
from build_pack import files,WARDEN_MODELS
from build_bedrock import files as bedrock_files,display_mappings
class WardenModelTest(unittest.TestCase):
 def test_all_poses_resolve_in_java_and_bedrock(self):
  java=files();bedrock=bedrock_files()
  for name in WARDEN_MODELS:
   m=json.loads(java['assets/yetiboss/models/boss/'+name+'.json'])
   self.assertIn('yetiboss:'+name,display_mappings())
   self.assertIn('models/entity/'+name+'.geo.json',bedrock)
   for e in m['elements']:
    self.assertTrue(all(e['to'][i]>e['from'][i] for i in range(3)))
    for face in e['faces'].values():
     path=m['textures'][face['texture'][1:]]
     self.assertIn('assets/'+path.replace(':','/textures/')+'.png',java)
 def test_walk_moves_limbs_and_preserves_glowing_core(self):
  from warden_model import model
  self.assertNotEqual(model(frame=6),model(frame=18))
  for frame in range(24):
   m=model(frame)
   self.assertTrue(any(e.get('light_emission')==15 for e in m['elements']))
   self.assertEqual(0,min(e['from'][1] for e in m['elements']))

 def test_new_animations_move_and_settle(self):
  from warden_model import model
  for kind,count in (('idle',8),('hurt',8),('emerge',8),('roar',8),('sniff',8),('strike',12)):
   self.assertNotEqual(model(0,kind),model(count//2,kind),kind)
  rest=model()['elements'];strike=model(11,'strike')['elements']
  self.assertEqual([(e['from'],e['to']) for e in rest],[(e['from'],e['to']) for e in strike])
  self.assertTrue(all(e.get('rotation',{}).get('angle',0)==0 for e in strike))
  self.assertEqual(rest,model(7,'emerge')['elements'])
  self.assertEqual(rest,model(7,'hurt')['elements'])
