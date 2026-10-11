import math,unittest
from boss_model import model
class SolidTorsoTest(unittest.TestCase):
 def test_center_torso_has_material_on_both_sides_through_all_poses(self):
  def inside(e,p):
   r=e.get('rotation');q=list(p)
   if r:
    o=r['origin'];q=[q[i]-o[i] for i in range(3)];angle=math.radians(-r['angle']);c,s=math.cos(angle),math.sin(angle)
    if r['axis']=='x':q[1],q[2]=q[1]*c-q[2]*s,q[1]*s+q[2]*c
    elif r['axis']=='z':q[0],q[1]=q[0]*c-q[1]*s,q[0]*s+q[1]*c
    q=[q[i]+o[i] for i in range(3)]
   return all(e['from'][i]<=q[i]<=e['to'][i] for i in range(3))
  poses=[model()]+[model(attack=i,kind=k) for k in ('slam','swipe','throw','roar') for i in range(8)]
  for mesh in poses:
   for y in (3.5,4.5,5.5,6.5,7.5,8.5,9.5):
    for x in (7.9,8.1):self.assertTrue(any(inside(e,(x,y,8.8)) for e in mesh['elements']),(x,y))

 def test_barrel_torso_has_closed_front_and_back_in_all_poses(self):
  # Test the visible body width, not just two samples along the center seam.
  poses=[model()]+[model(attack=i,kind=k) for k in ('slam','swipe','throw','roar','whirl') for i in range(8)]
  poses+=[model(frame=i,kind=k) for k in ('walk','gallop') for i in range(24)]
  for mesh in poses:
   core=[e for e in mesh['elements'] if e.get('name')=='torso_core']
   self.assertEqual(2,len(core))
   left,right=sorted(core,key=lambda e:e['from'][0])
   self.assertEqual(left['to'][0],right['from'][0])
   self.assertEqual(left['from'][1:],right['from'][1:])
   self.assertEqual(left['to'][1:],right['to'][1:])
   for e in core:
    self.assertNotIn('rotation',e)
    self.assertTrue({'north','south','up','down'}.issubset(e['faces']))
   self.assertGreater(right['to'][0]-left['from'][0],7)
   self.assertGreater(left['to'][2]-left['from'][2],5)

 def test_walk_retains_the_same_surface_topology(self):
  count=len(model()['elements'])
  for kind in ('walk','gallop'):
   for i in range(24):self.assertEqual(count,len(model(frame=i,kind=kind)['elements']))

 def test_eyes_share_height_and_front_plane(self):
  m=model();eyes={}
  for e in m['elements']:
   if e['faces'].get('north',{}).get('texture') in ('#ice_face','#optic'):eyes[e['faces']['north']['texture']]=e
  self.assertEqual(eyes['#ice_face']['from'][1:],eyes['#optic']['from'][1:])
  self.assertEqual(eyes['#ice_face']['to'][1:],eyes['#optic']['to'][1:])

 def test_nose_front_is_closed_across_center_in_every_father_pose(self):
  poses=[model()]+[model(attack=i,kind=k) for k in ('slam','swipe','throw','roar') for i in range(8)]
  poses+=[model(frame=i,kind=k) for k in ('walk','gallop') for i in range(24)]
  for mesh in poses:
   front=[e for e in mesh['elements'] if e['faces'].get('north',{}).get('texture')=='#muzzle']
   self.assertEqual(1,len(front))
   organic=front[0];seam=organic['to'][0]
   metal=[e for e in mesh['elements'] if e['faces'].get('north',{}).get('texture')=='#steel'
          and abs(e['from'][0]-seam)<1e-5 and abs(e['from'][2]-organic['from'][2])<1e-5]
   self.assertEqual(1,len(metal))
   self.assertEqual(organic['from'][1:],metal[0]['from'][1:])
   self.assertEqual(organic['to'][1:],metal[0]['to'][1:])

 def test_head_rear_and_crown_are_closed_at_the_half_seam(self):
  poses=[model()]+[model(attack=i,kind=k) for k in ('slam','swipe','throw','roar','whirl') for i in range(8)]
  poses+=[model(frame=i,kind=k) for k in ('walk','gallop') for i in range(24)]
  for mesh in poses:
   skull=sorted((e for e in mesh['elements'] if e.get('name')=='skull_core'),key=lambda e:e['from'][0])
   self.assertEqual(2,len(skull))
   left,right=skull
   self.assertEqual(left['to'][0],right['from'][0])
   self.assertEqual(left['from'][1:],right['from'][1:])
   self.assertEqual(left['to'][1:],right['to'][1:])
   for e in skull:self.assertTrue({'north','south','up','down'}.issubset(e['faces']))
