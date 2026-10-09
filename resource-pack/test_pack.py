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
    if 'rotation' in element:self.assertTrue(-45<=element['rotation']['angle']<=45)
 def test_eyes_only_appear_on_front_in_every_pose(self):
  for name in MODELS:
   m=json.loads(self.java['assets/yetiboss/models/boss/'+name+'.json'])
   eye_faces=[(side,face) for e in m['elements'] for side,face in e['faces'].items() if face['texture']=='#ice_face']
   self.assertEqual(['north'],[side for side,face in eye_faces],name)
 def test_no_overlapping_coplanar_surfaces_in_any_pose(self):
  axes={'north':(2,False),'south':(2,True),'west':(0,False),'east':(0,True),'down':(1,False),'up':(1,True)}
  for name in MODELS:
   elements=json.loads(self.java['assets/yetiboss/models/boss/'+name+'.json'])['elements']
   for i,a in enumerate(elements):
    for b in elements[:i]:
     if a.get('rotation')!=b.get('rotation'):continue
     for side,(axis,high) in axes.items():
      if side not in a['faces'] or side not in b['faces']:continue
      bound='to' if high else 'from'
      if abs(a[bound][axis]-b[bound][axis])>1e-8:continue
      overlap=all(min(a['to'][k],b['to'][k])-max(a['from'][k],b['from'][k])>1e-8 for k in range(3) if k!=axis)
      self.assertFalse(overlap,(name,i,side))
 def test_approved_shape_and_scream_teeth(self):
  rest=model();roar=model(attack=3,kind='roar')
  self.assertEqual(0,min(e['from'][1] for e in rest['elements']))
  self.assertTrue(any(e['faces']['north']['texture']=='#horn' for e in rest['elements']))
  self.assertFalse(any(e['faces']['north']['texture']=='#tooth' for e in rest['elements']))
  teeth=[e for e in roar['elements'] if e['faces']['north']['texture']=='#tooth']
  self.assertGreater(len(teeth),6)
  self.assertTrue(all(e['to'][2]<=3.65 for e in teeth))
 def test_knuckle_gait_has_alternating_lifts_and_short_steps(self):
  rest=model()['elements']
  left=next(i for i,e in enumerate(rest) if e['from']==[.85,.1,3.6])
  right=next(i for i,e in enumerate(rest) if e['from']==[12.15,.1,3.6])
  front=model(frame=6)['elements'];back=model(frame=18)['elements']
  self.assertGreater(front[left]['from'][1],front[right]['from'][1])
  self.assertGreater(back[right]['from'][1],back[left]['from'][1])
  self.assertAlmostEqual(front[left]['rotation']['angle'],10)
  self.assertAlmostEqual(front[right]['rotation']['angle'],-10)
 def test_attack_poses_raise_both_arms(self):
  rotations=[e['rotation'] for e in model(attack=3)['elements'] if 'rotation' in e]
  for pivot in ([3.5,10.3,7.2],[12.5,10.3,7.2]):
   self.assertTrue(any(r['origin']==pivot and r['axis']=='x' and r['angle']==45 for r in rotations))
 def test_custom_sounds_are_in_both_packs(self):
  for name in ('idle','angry','spawn','death','hurt_1','hurt_2','grab_slam'):
   data=self.java['assets/yetiboss/sounds/'+name+'.ogg']
   self.assertTrue(data.startswith(b'OggS'))
   self.assertIn(name,json.loads(self.java['assets/yetiboss/sounds.json']))
   self.assertIn('yetiboss.'+name,json.loads(self.bedrock['sounds/sound_definitions.json'])['sound_definitions'])
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
  java=raw(self.java['assets/yetiboss/textures/boss/father_fur.png'])
  bedrock=raw(self.bedrock['textures/yetiboss/giant_yeti.png'])
  width=len(names)*64+1
  for y in range(16):
   self.assertEqual(java[y*65+1:y*65+65],bedrock[y*width+1+tile*64:y*width+1+(tile+1)*64])
  self.assertGreater(len(set(java[1:65])),4)

 def test_roar_mouth_is_in_front_of_chest_and_mesh_is_compact(self):
  m=model(attack=3,kind='roar');self.assertLess(len(m['elements']),120)
  cavity=[e for e in m['elements'] if e['faces']['north']['texture']=='#scream']
  self.assertLess(max(e['to'][2] for e in cavity),6)

 def test_mother_has_distinct_shape_palette_and_every_animation(self):
  from boss_model import mother_model,texture_color
  father,mother=model(),mother_model()
  self.assertNotEqual(father['elements'],mother['elements'])
  self.assertLess(mother['elements'][0]['to'][0]-mother['elements'][0]['from'][0],12.4-3.6)
  self.assertEqual(13.1,max(e['to'][1] for e in mother['elements']))
  self.assertEqual(0,min(e['from'][1] for e in mother['elements']))
  self.assertNotEqual(texture_color('ice_face',3,10),texture_color('mother_ice_face',3,10))
  for texture in mother['textures'].values():self.assertIn('/mother_',texture)
  for name in MODELS:
   if name.startswith('giant_yeti'):
    counterpart=name.replace('giant_yeti','mother_yeti')
    if '_gallop_' in name or ('_walk_' in name and int(name.rsplit('_',1)[1])>=12):continue
    self.assertIn('assets/yetiboss/items/'+counterpart+'.json',self.java)
    self.assertIn('attachables/'+counterpart+'.json',self.bedrock)
 def test_mother_walk_keeps_shared_rig_attached_to_slimmer_body(self):
  from boss_model import mother_model,legacy_model
  father,mother=legacy_model(frame=3),mother_model(frame=3)
  f=[e['rotation'] for e in father['elements'] if 'rotation' in e and e['rotation']['axis']=='x']
  m=[e['rotation'] for e in mother['elements'] if 'rotation' in e and e['rotation']['axis']=='x']
  self.assertEqual(len(f),len(m))
  for a,b in zip(f,m):
   self.assertEqual(a['angle'],b['angle'])
   self.assertEqual(round(8+(a['origin'][0]-8)*.9,6),b['origin'][0])
   self.assertEqual(a['origin'][1:],b['origin'][1:])

 def test_father_antler_branches_form_two_connected_groups(self):
  import math
  def polygon(e):
   a,b=e['from'],e['to'];r=e['rotation'];ox,oy,_=r['origin']
   c,s=math.cos(math.radians(r['angle'])),math.sin(math.radians(r['angle']))
   return [(ox+(x-ox)*c-(y-oy)*s,oy+(x-ox)*s+(y-oy)*c) for x,y in ((a[0],a[1]),(b[0],a[1]),(b[0],b[1]),(a[0],b[1]))]
  def intersects(a,b):
   for poly in (a,b):
    for i,(x,y) in enumerate(poly):
     nx,ny=poly[(i+1)%4];axis=(y-ny,nx-x)
     aa=[x*axis[0]+y*axis[1] for x,y in a];bb=[x*axis[0]+y*axis[1] for x,y in b]
     if min(max(aa),max(bb))-max(min(aa),min(bb))<=1e-8:return False
   return True
  for pose in (model(),model(frame=3),model(attack=3)):
   horns=[e for e in pose['elements'] if e['faces']['north']['texture']=='#horn']
   for right in (False,True):
    group=[polygon(e) for e in horns if (e['from'][0]>8)==right]
    seen={0}
    while True:
     expanded=seen|{j for j in range(len(group)) if any(intersects(group[i],group[j]) for i in seen)}
     if expanded==seen:break
     seen=expanded
    self.assertEqual(len(group),len(seen),'Floating antler segment')

 def test_cyborg_parts_follow_arm_rig_and_optic_is_front_only(self):
  for frame,attack in ((None,None),(3,None),(9,None),(None,3)):
   m=model(frame=frame,attack=attack)
   arm=m['elements'][next(i for i,e in enumerate(model()['elements']) if e['from']==[12.15,.1,3.6])]
   piston=m['elements'][next(i for i,e in enumerate(model()['elements']) if e['from']==[12.18,3.2,4.08])]
   self.assertEqual(arm.get('rotation'),piston.get('rotation'))
   optics=[side for e in m['elements'] for side,f in e['faces'].items() if f['texture']=='#optic']
   self.assertEqual(['north'],optics)
   mats={f['texture'] for e in m['elements'] for f in e['faces'].values()}
   self.assertTrue({'#fur','#steel','#mechanism','#reactor','#cable'}<=mats)

 def test_walk_has_small_continuous_steps_and_matching_cyborg_pistons(self):
  angles=[]
  for i in range(24):
   m=model(frame=i)
   fist=m['elements'][next(i for i,e in enumerate(model()['elements']) if e['from']==[12.15,.1,3.6])]
   piston=m['elements'][next(i for i,e in enumerate(model()['elements']) if e['from']==[12.18,3.2,4.08])]
   self.assertEqual(fist.get('rotation'),piston.get('rotation'))
   angles.append(fist.get('rotation',{}).get('angle',0))
   self.assertIn('assets/yetiboss/items/giant_yeti_walk_'+str(i)+'.json',self.java)
  self.assertGreater(len(set(angles)),10)
  self.assertLess(max(abs(angles[(i+1)%24]-a) for i,a in enumerate(angles)),6)
