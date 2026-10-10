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
   for y in (4.6,5.5,6.5,7.5,8.5,9.5,10.5):
    for x in (7.9,8.1):self.assertTrue(any(inside(e,(x,y,8.8)) for e in mesh['elements']),(x,y))

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
