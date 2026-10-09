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
    self.assertTrue(all(-16<=a<=b<=32 for a,b in zip(e['from'],e['to'])))
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

 def test_tools_extend_forward_from_palm_instead_of_into_forearm(self):
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
    self.assertLess(v[2],-.95) # Out in front of the palm, away from the arm.
    self.assertLess(abs(v[1]),.25)
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
    if name.startswith('frostbow'):
     target=((1 if left else -1),-2,2.5) if hand.startswith('thirdperson') else (-1.13 if left else 1.13,3.2,1.13)
    else:
     target=(0,-2,1) if hand.startswith('thirdperson') else (-1.13 if left else 1.13,-1.3,-.5)
    for a,b in zip(actual,target):self.assertAlmostEqual(a,b,places=5)
 def test_bow_matches_vanilla_basis_in_each_hand_and_draw_stage(self):
  import math
  def rotate(v,angles):
   x,y,z=v
   for axis,degrees in reversed(list(zip('xyz',angles))):
    c=math.cos(math.radians(degrees));s=math.sin(math.radians(degrees))
    if axis=='z':x,y=x*c-y*s,x*s+y*c
    elif axis=='y':x,z=x*c+z*s,-x*s+z*c
    else:y,z=y*c-z*s,y*s+z*c
   return x,y,z
  vanilla={'thirdperson_righthand':[-80,260,-40], 'thirdperson_lefthand':[-80,-280,40],
           'firstperson_righthand':[0,-90,25], 'firstperson_lefthand':[0,90,-25]}
  for name in ('frostbow','frostbow_pull_0','frostbow_pull_1','frostbow_pull_2'):
   for hand,baseline in vanilla.items():
    angles=list(model(name)['display'][hand]['rotation']);left=hand.endswith('lefthand')
    baseline=list(baseline)
    if left:
     angles[1]*=-1;angles[2]*=-1;baseline[1]*=-1;baseline[2]*=-1
    for direction in ((1,0,0),(0,1,0),(0,0,1)):
     expected=rotate(rotate(direction,[0,0,135]),baseline)
     actual=rotate(direction,angles)
     for a,b in zip(actual,expected):self.assertAlmostEqual(a,b)
 def test_bedrock_gear_is_originated_at_actual_grip(self):
  from gear_model import grip_point
  for name in GEAR_MODELS:
   m=model(name);gx,gy,gz=grip_point(name)
   geo=json.loads(self.bedrock['models/entity/'+name+'.geo.json'])['minecraft:geometry'][0]
   for element,cube in zip(m['elements'],geo['bones'][0]['cubes']):
    self.assertEqual([gx-element['to'][0],element['from'][1]-gy,element['from'][2]-gz],cube['origin'])
 def test_imported_geometry_and_texture_preservation(self):
  from gear_model import imported,texture
  from png_codec import decode
  for name,count in (('frostfang',24),('frostpickaxe',34),('frostbow',17)):
   original=imported(name)
   self.assertEqual(count,len(model(name)['elements']))
   self.assertEqual(original['elements'],model(name)['elements'])
   self.assertEqual(original['textures'],model(name)['textures'])
   for material in original['textures']:
    w,h,p=decode(texture(material));self.assertEqual((64,64),(w,h));self.assertEqual(w*h*4,len(p))
 def test_compound_rotations_preserved_for_bow(self):
  rotations=[e['rotation'] for e in model('frostbow')['elements'] if 'rotation' in e]
  self.assertTrue(any(sum(abs(r.get(axis,0))>1e-5 for axis in 'xyz')>1 for r in rotations))
 def test_bedrock_imported_texture_atlas_keeps_full_face_resolution(self):
  from png_codec import decode
  for name in GEAR_MODELS:
   m=model(name);w,h,_=decode(self.bedrock['textures/yetiboss/'+name+'.png'])
   self.assertEqual((64*len(m['textures']),64),(w,h))
   geo=json.loads(self.bedrock['models/entity/'+name+'.geo.json'])['minecraft:geometry'][0]
   self.assertEqual(w,geo['description']['texture_width'])
   self.assertEqual(h,geo['description']['texture_height'])
