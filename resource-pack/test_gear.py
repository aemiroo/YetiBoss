import json,unittest
from build_pack import files
from build_bedrock import files as bedrock_files,mappings
from gear_model import GEAR_MODELS,GEAR_ITEMS,model
class GearPackTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.java=files();cls.bedrock=bedrock_files()
 def test_model_textures_and_all_hand_transforms_resolve(self):
  for name in GEAR_MODELS:
   m=json.loads(self.java['assets/yetiboss/models/gear/'+name+'.json'])
   for texture in m['textures'].values():self.assertIn('assets/'+texture.replace(':','/textures/')+'.png',self.java)
   for transform in ('gui','ground','fixed','firstperson_righthand','firstperson_lefthand','thirdperson_righthand','thirdperson_lefthand'):self.assertIn(transform,m['display'])
   for e in m['elements']:
    self.assertTrue(all(0<=a<b<=16 for a,b in zip(e['from'],e['to'])))
   self.assertIn('attachables/'+name+'.json',self.bedrock)
 def test_bow_draw_stages_change_string_and_keep_own_namespace(self):
  definition=json.loads(self.java['assets/yetiboss/items/frostbow.json'])['model']
  self.assertEqual('minecraft:using_item',definition['property'])
  pulling=definition['on_true'];self.assertEqual('minecraft:use_duration',pulling['property'])
  refs=[definition['on_false'],pulling['fallback']]+[e['model'] for e in pulling['entries']]
  for ref in refs:
   self.assertTrue(ref['model'].startswith('yetiboss:gear/'))
   self.assertIn('assets/'+ref['model'].replace(':','/models/')+'.json',self.java)
  self.assertEqual(4,len({json.dumps(model(name)) for name in ('frostbow','frostbow_pull_0','frostbow_pull_1','frostbow_pull_2')}))
 def test_bedrock_maps_real_item_types_and_binds_gear_to_hand(self):
  item_mappings=mappings()['items']
  for name,base in GEAR_ITEMS.items():
   self.assertEqual('yetiboss:'+name,item_mappings[base][0]['model'])
   geo=json.loads(self.bedrock['models/entity/'+name+'.geo.json'])
   self.assertEqual('query.item_slot_to_bone_name(context.item_slot)',geo['minecraft:geometry'][0]['bones'][0]['binding'])
   self.assertIn('textures/yetiboss/'+name+'_icon.png',self.bedrock)
