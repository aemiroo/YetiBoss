import unittest
from boss_model import model,gorilla_point
from build_pack import FATHER_MODELS,MODELS
class SkillModelTest(unittest.TestCase):
 def test_whirlwind_arm_and_piston_share_a_smooth_outward_rig(self):
  previous=0
  for frame in range(8):
   elements=model(attack=frame,kind='whirl')['elements']
   piston=next(e for e in elements if e['from']==gorilla_point([12.18,3.2,4.08],True))
   rotation=piston.get('rotation',{})
   angle=rotation.get('angle',0)
   self.assertLessEqual(abs(angle-previous),7)
   if rotation:
    self.assertEqual('z',rotation['axis']);self.assertEqual(gorilla_point([12.5,10.3,7.2],True),rotation['origin'])
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
  self.assertGreater(max(e['to'][0] for e in elements if e.get('name')=='arm_r')-min(e['from'][0] for e in arms),14)
 def test_reactor_glow_retains_solid_geometry(self):
  mesh=model();glow=[e for e in mesh['elements'] if e.get('light_emission')]
  self.assertGreaterEqual(len(glow),8)
  self.assertTrue(all(any(f['texture']=='#reactor' for f in e['faces'].values()) for e in glow))
  self.assertTrue(all(e['to'][i]>e['from'][i] for e in glow for i in range(3)))
