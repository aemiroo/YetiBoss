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

 def test_upright_tools_point_up_in_both_third_person_hands(self):
  import math
  def rotate(v,axis,degrees):
   x,y,z=v;c=math.cos(math.radians(degrees));s=math.sin(math.radians(degrees))
   return ((x,y*c-z*s,y*s+z*c) if axis=='x' else
           (x*c+z*s,y,-x*s+z*c) if axis=='y' else (x*c-y*s,x*s+y*c,z))
  for name in ('frostfang','frostpickaxe'):
   for hand in ('thirdperson_righthand','thirdperson_lefthand'):
    pose=model(name)['display'][hand];v=(0,1,0)
    pose=dict(pose)
    if hand.endswith('lefthand'):pose['rotation']=[pose['rotation'][0],-pose['rotation'][1],-pose['rotation'][2]]
    for axis,degrees in reversed(list(zip('xyz',pose['rotation']))):v=rotate(v,axis,degrees)
    # Minecraft's third-person item holder applies Y=180 and X=-90.
    v=rotate(rotate(v,'y',180),'x',-90)
    self.assertLess(v[1],-.99) # Render-space negative Y is upward.
 def test_bow_has_distinct_hand_pose_and_draw_stages_keep_same_grip(self):
  bow=model('frostbow')['display'];sword=model('frostfang')['display']
  self.assertNotEqual(sword['thirdperson_righthand'],bow['thirdperson_righthand'])
  for name in ('frostbow_pull_0','frostbow_pull_1','frostbow_pull_2'):
   self.assertEqual(bow,model(name)['display'])
   self.assertEqual(model('frostbow')['elements'][0],model(name)['elements'][0])

 def test_grip_reaches_palm_in_every_hand_and_draw_stage(self):
  import math
  from gear_model import grip_point
  def rotate(v,axis,degrees):
   x,y,z=v;c=math.cos(math.radians(degrees));s=math.sin(math.radians(degrees))
   return ((x,y*c-z*s,y*s+z*c) if axis=='x' else
           (x*c+z*s,y,-x*s+z*c) if axis=='y' else (x*c-y*s,x*s+y*c,z))
  for name in GEAR_MODELS:
   for hand in ('thirdperson_righthand','thirdperson_lefthand','firstperson_righthand','firstperson_lefthand'):
    pose=model(name)['display'][hand];left=hand.endswith('lefthand')
    rotations=list(pose['rotation']);translation=list(pose['translation'])
    if left:rotations[1]*=-1;rotations[2]*=-1;translation[0]*=-1
    v=tuple(p-8 for p in grip_point(name))
    for axis,degrees in reversed(list(zip('xyz',rotations))):v=rotate(v,axis,degrees)
    actual=[p*scale+t for p,scale,t in zip(v,pose['scale'],translation)]
    target=(0,-2,1) if hand.startswith('thirdperson') else (-1.13 if left else 1.13,-1.3,-.5)
    for a,b in zip(actual,target):self.assertAlmostEqual(a,b,places=5)
 def test_bedrock_gear_is_originated_at_actual_grip(self):
  from gear_model import grip_point
  for name in GEAR_MODELS:
   m=model(name);gx,gy,gz=grip_point(name)
   geo=json.loads(self.bedrock['models/entity/'+name+'.geo.json'])['minecraft:geometry'][0]
   for element,cube in zip(m['elements'],geo['bones'][0]['cubes']):
    self.assertEqual([gx-element['to'][0],element['from'][1]-gy,element['from'][2]-gz],cube['origin'])
 def test_frost_materials_have_cracks_wrapping_and_highlights(self):
  from gear_model import color
  self.assertNotEqual(color('gear_ice',3,0),color('gear_ice',4,0))
  self.assertGreater(color('gear_steel',0,8)[0],color('gear_steel',8,8)[0])
  self.assertNotEqual(color('gear_grip',8,0),color('gear_grip',8,2))
  self.assertGreater(color('gear_core',6,7)[1],color('gear_core',2,7)[1])
