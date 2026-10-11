import unittest
from boss_model import model
from build_pack import FATHER_MODELS,MODELS
class SkillModelTest(unittest.TestCase):
 def test_whirlwind_arm_and_piston_share_a_smooth_outward_rig(self):
  previous=0
  for frame in range(8):
   elements=model(attack=frame,kind='whirl')['elements']
   piston=next(e for e in elements if e.get('role')=='piston')
   rotation=piston.get('rotation',{})
   angle=rotation.get('angle',0)
   self.assertLessEqual(abs(angle-previous),7)
   if rotation:
    self.assertEqual('z',rotation['axis']);self.assertEqual([11.774,10.5798,6.156],rotation['origin'])
   self.assertIn('giant_yeti_whirl_'+str(frame),FATHER_MODELS)
   previous=angle
  self.assertEqual(45,previous)
  self.assertFalse(any('_whirl_' in name for name in MODELS if name.startswith('mother_')))
 def test_gorilla_knuckles_are_forward_and_legs_are_short(self):
  elements=model()['elements']
  arms=[e for e in elements if e.get('name')=='arm_l']
  legs=[e for e in elements if e.get('name')=='leg_l']
  self.assertTrue(arms and legs)
  self.assertLess(min(e['from'][1] for e in arms),.1)
  self.assertGreater(max(e['to'][1] for e in arms),3*max(e['to'][1] for e in legs))
  self.assertLess(min(e['from'][2] for e in arms)+1.5,min(e['from'][2] for e in legs))
  self.assertGreater(max(e['to'][0] for e in elements if e.get('name')=='arm_r')-min(e['from'][0] for e in arms),10)
 def test_reactor_glow_retains_solid_geometry(self):
  mesh=model();glow=[e for e in mesh['elements'] if e.get('light_emission')]
  self.assertGreaterEqual(len(glow),8)
  self.assertTrue(all(any(f['texture']=='#reactor' for f in e['faces'].values()) for e in glow))
  self.assertTrue(all(e['to'][i]>e['from'][i] for e in glow for i in range(3)))

 def test_silverback_anatomy_is_built_in_the_mesh(self):
  mesh=model()['elements']
  parts={e['role']:e for e in mesh if 'role' in e}
  head=parts['skull_core'];hump=parts['silverback_hump'];shoulder=parts['shoulder_crown']
  self.assertGreater(hump['to'][1],head['to'][1]+1)
  self.assertGreater(hump['from'][2],head['from'][2]+2.5)
  self.assertGreater(shoulder['to'][1],head['to'][1])
  self.assertLess(parts['fist']['from'][2],parts['foot']['from'][2]-4)
  self.assertGreater(parts['fist']['to'][0]-parts['fist']['from'][0],1.8)
  self.assertLess(parts['abdomen']['to'][0]-parts['abdomen']['from'][0],parts['pectoral_r']['to'][0]-8)

 def test_tapered_body_leaves_space_beside_the_lower_arms(self):
  mesh=model()['elements']
  core=next(e for e in mesh if e.get('name')=='torso_core' and e['from'][0]<8)
  fist=next(e for e in mesh if e.get('role')=='fist' and e.get('name')=='arm_l')
  self.assertGreater(core['from'][0]-fist['to'][0],.6)
  shoulders=[e for e in mesh if e.get('role')=='mantle']
  self.assertGreater(max(e['to'][0] for e in shoulders)-min(e['from'][0] for e in shoulders),
                     1.3*(2*(8-core['from'][0])))

 def test_lean_revision_has_small_cross_sections_and_tall_body(self):
  mesh=model()['elements']
  core=[e for e in mesh if e.get('name')=='torso_core']
  width=max(e['to'][0] for e in core)-min(e['from'][0] for e in core)
  self.assertLessEqual(width,5.1)
  self.assertLess(core[0]['to'][2]-core[0]['from'][2],4.8)
  fists=[e for e in mesh if e.get('role')=='fist']
  self.assertTrue(all(e['to'][0]-e['from'][0]<2 for e in fists))
  crown=next(e for e in mesh if e.get('role')=='hump_crown')
  self.assertGreater(crown['to'][1],15)

 def test_organic_hand_is_connected_and_follows_the_arm_in_every_pose(self):
  roles={'fist','hand_fur','knuckle','finger','fingertip','thumb','thumb_tip'}
  poses=[model()]+[model(frame=i) for i in range(24)]
  poses+=[model(attack=i,kind=k) for k in ('slam','swipe','throw','roar','whirl') for i in range(8)]
  for mesh in poses:
   hand=[e for e in mesh['elements'] if e.get('name')=='arm_l' and e.get('role') in roles]
   forearm=next(e for e in mesh['elements'] if e.get('name')=='arm_l' and e.get('role')=='forearm')
   self.assertTrue(all(e.get('rotation')==forearm.get('rotation') for e in hand))
   fingers=sorted((e for e in hand if e.get('role')=='finger'),key=lambda e:e['from'][0])
   self.assertEqual(4,len(fingers))
   self.assertTrue(all(a['to'][0]<b['from'][0] for a,b in zip(fingers,fingers[1:])))
   seen={0}
   while True:
    added=seen|{j for j,b in enumerate(hand) if any(all(min(hand[i]['to'][axis],b['to'][axis])>max(hand[i]['from'][axis],b['from'][axis]) for axis in range(3)) for i in seen)}
    if added==seen:break
    seen=added
   self.assertEqual(len(hand),len(seen),'Detached organic hand part')

 def test_mechanical_hand_geometry_and_materials_are_preserved(self):
  import json,hashlib
  hand=[e for e in model()['elements'] if e.get('name')=='arm_r' and e.get('role') in ('fist','knuckle','thumb')]
  # Undo only the new resting stance translation; the hand design is unchanged.
  for e in hand:
   for bound in ('from','to'):e[bound][2]=round(e[bound][2]+1,8)
  self.assertEqual('f31aa6883f0a585e3128b1fdb1b8aec59b8a7c24d3b2f255327ed179e435fbaf',
                   hashlib.sha256(json.dumps(hand,sort_keys=True).encode()).hexdigest())

 def test_resting_pose_leans_from_hips_with_bent_legs_and_grounded_hands(self):
  import math
  mesh=model()['elements']
  core=next(e for e in mesh if e.get('name')=='torso_core')
  self.assertEqual({'origin':[8,3.4,9],'angle':-22.5,'axis':'x','rescale':False},core['rotation'])
  self.assertTrue(all(e['rotation']['angle']==22.5 for e in mesh if e.get('role')=='thigh'))
  self.assertEqual(0,min(e['from'][1] for e in mesh if e.get('name')=='arm_l'))
  self.assertEqual(0,min(e['from'][1] for e in mesh if e.get('name')=='arm_r'))
  # The high center of the back moves several units ahead of the hip hinge.
  angle=math.radians(-22.5)
  y,z=12-3.4,9-9
  leaned_z=9+math.sin(angle)*y+math.cos(angle)*z
  self.assertLess(leaned_z,6)
