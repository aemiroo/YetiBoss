"""Asset conversion checks for the actual user GLB, separate from fallback anatomy checks."""
import copy,hashlib,json,math,unittest
from imported_father import DATA,TEXTURE_BYTES,model,transforms,point,vec,add,SCALE,LEFT,RIGHT,HEAD,HAND,BONES
from mesh_preview import rotate
from png_codec import decode

def corners(e):
 r=e.get('rotation',{});o=r.get('origin',[0,0,0]);result=[]
 for x in (e['from'][0],e['to'][0]):
  for y in (e['from'][1],e['to'][1]):
   for z in (e['from'][2],e['to'][2]):result.append(add(rotate((x-o[0],y-o[1],z-o[2]),r),o))
 return result
class ImportedFatherTest(unittest.TestCase):
 def test_asset_contains_original_geometry_hierarchy_and_all_six_clips(self):
  self.assertEqual(70,DATA['source_meshes']);self.assertRegex(DATA['source_sha256'],r'^[0-9a-f]{64}$')
  self.assertEqual({'idle','walk','smash','attack1','attack2','death'},set(DATA['clips']))
  self.assertEqual(70,len({c['node'] for c in DATA['cubes']}))
  self.assertGreater(len(DATA['nodes']),150)
  for clip in DATA['clips'].values():
   self.assertGreater(clip['duration'],0)
   for channel in clip['channels']:
    self.assertIn(channel['node'],range(len(DATA['nodes'])))
    self.assertEqual(len(channel['times']),len(channel['values']))
    self.assertEqual(sorted(channel['times']),channel['times'])

 def test_exported_corners_match_source_cuboids_in_every_attack_and_gait(self):
  poses=[(None,None,'slam')]+[(i,None,k) for k in ('walk','gallop','idle') for i in range(24)]+[(None,i,k) for k in ('slam','swipe','throw','roar','whirl') for i in range(8)]
  for frame,attack,kind in poses:
   m=model(frame,attack,kind);worlds=transforms(m['source_animation'],m['source_time'],kind,attack)
   for e in m['elements']:
    i=e['source_index']
    if i>=len(DATA['cubes']):continue
    c=DATA['cubes'][i];R,T=worlds[c['node']];expected=[]
    for x in (c['from'][0],c['to'][0]):
     for y in (c['from'][1],c['to'][1]):
      for z in (c['from'][2],c['to'][2]):expected.append(point(add(vec(R,[x,y,z]),T)))
    for actual,want in zip(corners(e),expected):
     self.assertLess(max(abs(a-b) for a,b in zip(actual,want)),2e-6,(frame,attack,kind,i))

 def test_original_uv_patches_are_used_on_the_organic_half(self):
  m=model();organic=[e for e in m['elements'] if e['source_index']<len(DATA['cubes']) and not DATA['cubes'][e['source_index']]['mechanical']]
  self.assertGreater(len(organic),30)
  for e in organic:
   source=DATA['cubes'][e['source_index']]
   self.assertEqual(source['faces'],{side:f['texture'][1:] for side,f in e['faces'].items()})
  self.assertGreater(len(TEXTURE_BYTES),200)
  for data in TEXTURE_BYTES.values():self.assertEqual((16,16),decode(data)[:2])

 def test_animation_mapping_uses_source_clips_and_idle_moves(self):
  for kind,clip in (('slam','smash'),('swipe','attack1'),('throw','attack2')):
   self.assertEqual(clip,model(attack=3,kind=kind)['source_animation'])
  for kind in ('walk','gallop'):self.assertEqual('walk',model(frame=3,kind=kind)['source_animation'])
  idle=[model(frame=i,kind='idle') for i in range(24)]
  self.assertTrue(all(m['source_animation']=='idle' for m in idle))
  self.assertGreater(len({json.dumps(m['elements']) for m in idle}),12)
  self.assertEqual(len(model()['elements']),len(idle[3]['elements']))

 def test_attack_loops_settle_at_their_starting_pose(self):
  for kind in ('slam','swipe','throw','whirl'):
   first=model(attack=0,kind=kind);last=model(attack=7,kind=kind)
   self.assertEqual(first['elements'],last['elements'],kind)
   if kind!='whirl':
    times=[model(attack=i,kind=kind)['source_time'] for i in range(8)]
    self.assertGreater(times[3],times[1]);self.assertGreater(times[4],times[6])

 def test_natural_pose_has_forward_shoulders_and_head_and_grounded_hands(self):
  worlds=transforms('idle',0);left=point(worlds[LEFT][1]);head=point(worlds[HEAD][1]);hip=point(worlds[BONES['left_leg_13']][1])
  self.assertGreater(hip[2]-left[2],4)
  self.assertLess(abs(left[1]-hip[1]),hip[2]-left[2])
  self.assertLess(head[2],left[2]-1)
  m=model()
  for side in ('arm_l','arm_r'):
   low=min(p[1] for e in m['elements'] if e['name']==side for p in corners(e))
   self.assertLess(abs(low),.12,(side,low))

 def test_approved_mechanical_hand_is_mounted_without_changing_its_faces_or_shape(self):
  for frame,attack,kind in ((None,None,'slam'),(4,None,'walk'),(None,3,'slam'),(None,7,'whirl')):
   m=model(frame,attack,kind);hand=[e for e in m['elements'] if 'approved_hand' in e]
   self.assertEqual(len(DATA['mechanical_hand']),len(hand))
   for e in hand:
    original=DATA['mechanical_hand'][e['approved_hand']]
    self.assertEqual(original['faces'],e['faces'])
    sizes=[e['to'][k]-e['from'][k] for k in range(3)]
    for k in range(3):self.assertAlmostEqual((original['to'][k]-original['from'][k])*SCALE*.8,sizes[k],places=6)
   self.assertTrue(all(e['source_node']==HAND for e in hand))

 def test_cyborg_reactor_and_optic_are_present_and_bound_to_source_nodes(self):
  m=model();self.assertGreaterEqual(sum(bool(e.get('light_emission')) for e in m['elements']),8)
  optic=[e for e in m['elements'] if e['role']=='optic'];self.assertEqual(1,len(optic));self.assertEqual(HEAD,optic[0]['source_node'])
  self.assertEqual(['north'],[side for side,f in optic[0]['faces'].items() if f['texture']=='#optic'])
  for m in (model(),model(attack=7,kind='whirl')):
   forearm=[e for e in m['elements'] if e['role'] in ('forearm_motor','piston','piston_outer')]
   self.assertEqual(3,len(forearm));self.assertEqual(1,len({e['source_node'] for e in forearm}))

 def test_optic_and_socket_follow_the_organic_eye_height(self):
  from imported_father import EYE_HEIGHT,EXTRAS
  organic=EYE_HEIGHT
  brow=DATA['nodes'][BONES['h_head_50']]['translation'][1]+DATA['cubes'][64]['from'][1]
  for role in ('optic','optic_socket'):
   cube=next(c for c in EXTRAS if c.get('role')==role)
   self.assertAlmostEqual(organic,(cube['from'][1]+cube['to'][1])/2)
   self.assertLess(cube['to'][1],brow)
  lens=next(c for c in EXTRAS if c.get('role')=='optic')
  source=DATA['cubes'][60]
  for axis in (0,1):
   self.assertAlmostEqual((source['to'][axis]-source['from'][axis])*3/16,lens['to'][axis]-lens['from'][axis])
  for frame,attack,kind in ((None,None,'slam'),(7,None,'idle'),(None,3,'slam'),(None,3,'whirl')):
   m=model(frame,attack,kind);r,t=transforms(m['source_animation'],m['source_time'],kind,attack)[HEAD]
   optic=next(e for e in m['elements'] if e['role']=='optic')
   center=[sum(p[k] for p in corners(optic))/8 for k in range(3)]
   expected=point(add(vec(r,[.3,organic,-.825]),t))
   self.assertLess(max(abs(a-b) for a,b in zip(center,expected)),2e-6)

 def test_chest_motor_and_eye_sockets_attach_to_retained_source_volumes(self):
  from imported_father import UPPER,FOREARM
  from imported_father import EYE_HEIGHT
  attachments=[(UPPER,[.265,.435,-.35]),(FOREARM,[0,-.26,-.195]),(HEAD,[.295,EYE_HEIGHT,-.73])]
  for frame,attack,kind in ((None,None,'slam'),(4,None,'walk'),(None,3,'slam'),(None,7,'whirl')):
   m=model(frame,attack,kind);worlds=transforms(m['source_animation'],m['source_time'],kind,attack)
   for node,local in attachments:
    R,T=worlds[node];world=add(vec(R,local),T);found=False
    for c in DATA['cubes']:
     r,t=worlds[c['node']];scale2=sum(r[k][0]**2 for k in range(3))
     q=[sum(r[k][axis]*(world[k]-t[k]) for k in range(3))/scale2 for axis in range(3)]
     if all(c['from'][k]-1e-6<=q[k]<=c['to'][k]+1e-6 for k in range(3)):found=True;break
    self.assertTrue(found,(node,frame,attack,kind))
