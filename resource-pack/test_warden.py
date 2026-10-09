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
