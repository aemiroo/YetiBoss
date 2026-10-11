"""Stocky glacier Yeti preview, built from shaped cuboids."""
import math
COLORS={'fur':(214,231,239,255),'fur_light':(243,250,253,255),'fur_shadow':(167,194,209,255),
 'ice':(65,187,223,255),'ice_dark':(35,116,156,255),'ice_light':(140,232,247,255),
 'ice_face':(64,190,222,255)}
COLORS['face_plain']=(46,67,78,255)
COLORS['muzzle']=(61,86,97,255)
COLORS['scream']=(61,86,97,255)
COLORS['tooth']=(231,235,216,255)
COLORS.update({'horn':(54,70,82,255),'nose':(78,89,100,255)})
BASE_MATERIALS=tuple(COLORS)
MOTHER_COLORS={'fur':(230,242,248,255),'fur_light':(250,253,255,255),
 'fur_shadow':(177,204,222,255),'horn':(87,164,198,255),'nose':(66,90,109,255),
 'face_plain':(49,70,91,255),'muzzle':(49,70,91,255),'scream':(49,70,91,255),
 'ice_face':(49,70,91,255)}
COLORS.update({'mother_'+n:MOTHER_COLORS.get(n,COLORS[n]) for n in BASE_MATERIALS})
def texture_color(mat,x,y):
 if mat.startswith('mother_'):
  original=mat[len('mother_'):]
  color=texture_color(original,x,y)
  if original=='ice_face':
   return (135,248,255) if color in ((255,145,99),(217,24,29)) else MOTHER_COLORS['ice_face'][:3]
  if original in ('muzzle','scream') and color in ((24,27,36),(17,19,27),(102,35,47)):return color
  if original.startswith('fur'):
   delta=color[0]-COLORS[original][0]
   return tuple(max(0,min(255,v+delta)) for v in MOTHER_COLORS[original][:3])
  return MOTHER_COLORS.get(original,COLORS[original])[:3]

 if mat in ('tooth','face_plain'):return COLORS[mat][:3]
 if mat in ('horn','nose'):
  c=COLORS[mat];return tuple(max(0,min(255,v+(((x//3+y//3)%3)-1)*4)) for v in c[:3])
 n=(x//2*17+y//2*31+x//2*y//2*11)%23
 if mat=='scream':
  if 2<=x<=13 and 1<=y<=12:
   if 6<=x<=9 and y==1:return (102,35,47)
   return (17,19,27)
  return (46,67,78)
 if mat=='muzzle':
  if 4<=x<=11 and y in (3,4):return (24,27,36)
  return (46,67,78)
 if mat=='ice_face':
  # Slanted eyes narrow toward the bridge of the nose.
  if 2<=x<=6 and 9<=y<=12-(x-2)//2:
   return (255,145,99) if y==9 and x in (4,11) else (217,24,29)
  if 9<=x<=13 and 9<=y<=12-(13-x)//2:
   return (255,145,99) if y==9 and x in (4,11) else (217,24,29)
  return (46,67,78)
 if mat.startswith('fur'):
  c=COLORS[mat][:3]
  delta=-13 if n<5 else 8 if n>19 else 0
  return tuple(max(0,min(255,v+delta)) for v in c)
 return COLORS['ice_dark' if n<5 else 'ice_light' if n>18 else 'ice'][:3]

def legacy_model(frame=None,attack=None,kind='slam'):
 pose='scream' if kind=='roar' and attack is not None else 'idle'
 phase=2*math.pi*(frame or 0)/12
 es=[]
 def box(a,b,mat,part=None,angle=0,pivot=None,axis='z'):
  if part and part.startswith('arm'):
   pivot=[3.5 if part=='arm_l' else 12.5,9,8]
   if attack is not None:
    progress=attack/7
    peak=math.sin(math.pi*progress)
    angle=-round(peak*2)*22.5;axis='x'
    if kind=='swipe' and part=='arm_r':angle=0
    if kind=='throw' and part=='arm_l':angle=0
    if kind=='roar':angle=-22.5
   elif frame is not None:
    angle=round(math.sin(phase))*22.5;axis='x'
  if part and part.startswith('leg') and frame is not None:
   pivot=[6 if part=='leg_l' else 10,4.5,8]
   angle=round(math.sin(phase))*22.5*(1 if part=='leg_l' else -1);axis='x'
  e={'from':list(a),'to':list(b),'faces':{f:{'uv':[0,0,16,16],'texture':'#'+mat} for f in ('north','south','east','west','up','down')}}
  if angle:e['rotation']={'origin':pivot,'angle':angle,'axis':axis,'rescale':False}
  es.append(e)
 # Broad hunched torso and forward head.
 box((4.1,4.6,6.0),(11.9,10.7,12.2),'fur')
 box((4.2,9,8.3),(11.8,12,12.5),'fur_light',angle=22.5,pivot=[8,10,9],axis='x')
 box((4.5,4.1,5.8),(11.5,6,11.1),'fur_shadow')
 for x,part in ((4.8,'leg_l'),(8.8,'leg_r')):
  box((x,1,6.6),(x+2.4,4.7,10.2),'fur',part)
  box((x-.02,0,5.7),(x+2.42,1.2,10.3),'fur_shadow',part)
 for right in (False,True):
  part='arm_r' if right else 'arm_l'
  def arm(a,b,mat):
   if right:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   box(a,b,mat,part)
  arm((.9,7.8,6),(4.3,11.1,10.8),'fur_light')
  arm((1.4,4.3,6.1),(3.95,7.8,10.6),'fur')
  arm((1.3,1.8,5.8),(4,4.7,10.4),'fur_light')
  arm((1.3,1.2,5.8),(4,1.8,10.4),'fur_shadow')
 box((5,9,4.2),(11,12.2,8.7),'fur_light')
 box((5.5,8.5,3.6),(10.5,10.5,4.4),'fur_shadow')
 es[-1]['faces']['north']['texture']='#scream' if pose=='scream' else '#muzzle'
 box((5.6,10,3.95),(10.4,11.4,4.25),'face_plain')
 es[-1]['faces']['north']['texture']='#ice_face'
 if pose=='scream':
  # Slim stepped fangs taper down; smaller incisors sit between them.
  for x in (6.2,9.4):
   box((x,9.55,3.35),(x+.4,9.95,3.65),'tooth')
   box((x+.07,9.22,3.35),(x+.33,9.55,3.65),'tooth')
   box((x+.13,9.02,3.35),(x+.27,9.22,3.65),'tooth')
  for x in (7.15,7.85,8.55):
   box((x,9.7,3.35),(x+.3,9.95,3.65),'tooth')
  for x in (6.65,7.45,8.25,9.05):
   box((x,8.7,3.35),(x+.25,8.9,3.65),'tooth')
 # Short squared muzzle with subtle warm nose.
 box((7.5,10.05,3.55),(8.5,10.7,3.95),'nose')
 for right in (False,True):
  def horn(a,b):
   if right:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   box(a,b,'horn')
  horn((4.3,10.8,3.5),(5.7,12.3,5.4))
  horn((4.1,12,4),(5.5,13.1,6.4))
  horn((4.4,12.02,6),(5.6,13,7.5))
 return {'elements':es,'textures':{n:'yetiboss:boss/'+n for n in BASE_MATERIALS},
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}


def mother_model(frame=None,attack=None,kind='slam'):
 """Distinct slender glacier guardian, with swept ice horns and shared rig."""
 m=legacy_model(frame,attack,kind)
 # Narrow the body and animated pivot positions together, so every limb stays attached.
 for e in m['elements']:
  for bound in ('from','to'):e[bound][0]=round(8+(e[bound][0]-8)*.9,6)
  if 'rotation' in e:e['rotation']['origin'][0]=round(8+(e['rotation']['origin'][0]-8)*.9,6)
 m['elements']=[e for e in m['elements'] if e['faces']['north']['texture']!='#horn']
 for right in (False,True):
  for a,b in (((4.5,10.8,4.6),(5.7,12.1,6.2)),
              ((3.6,11.75,5),(4.8,12.8,7)),
              ((3.7,12.6,6.5),(4.5,13.1,8))):
   if right:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   m['elements'].append({'from':list(a),'to':list(b),
    'faces':{f:{'uv':[0,0,16,16],'texture':'#horn'} for f in ('north','south','east','west','up','down')}})
 m['textures']={n:'yetiboss:boss/mother_'+n for n in BASE_MATERIALS}
 return m

# Father materials are independent from the Mother's established palette.
COLORS.update({'father_'+n:COLORS[n] for n in BASE_MATERIALS})
CYBORG_MATERIALS={'steel':(73,91,106,255),'metal_edge':(150,176,190,255),
 'mechanism':(28,39,49,255),'cable':(43,58,62,255),'reactor':(43,220,235,255),'optic':(246,66,47,255)}
COLORS.update({'father_'+n:c for n,c in CYBORG_MATERIALS.items()})
_previous_texture_color=texture_color
def texture_color(mat,x,y):
 if not mat.startswith('father_'):return _previous_texture_color(mat,x,y)
 name=mat[7:]
 if name in CYBORG_MATERIALS:
  c=CYBORG_MATERIALS[name][:3]
  if name in ('reactor','optic'):
   return tuple(min(255,v+35) for v in c) if 5<=x<=10 and 5<=y<=10 else c
  if name=='steel':
   delta=12 if x in (1,14) or y in (1,14) else ((x+3*y)%5-2)*2
  elif name=='metal_edge':delta=18 if x<5 else -15 if x>12 else 0
  else:delta=((x//2+y//2)%3-1)*7
  return tuple(max(0,min(255,v+delta)) for v in c)
 if name in ('fur','fur_light','fur_shadow','horn','muzzle'):
  base={'fur':(226,234,232),'fur_light':(238,242,235),'fur_shadow':(198,215,216),'horn':(207,219,207),'muzzle':(75,93,101)}[name]
  patch=((x//3)*7+(y//3)*11+(x//3)*(y//3))%9
  delta=(-10,-5,0,0,0,3,5,7,9)[patch]
  return tuple(max(0,min(255,c+delta)) for c in base)
 if name=='ice_face':
  return (255,156,76) if 3<=x<=12 and 5<=y<=10 else (37,53,56)
 if name=='nose':return (24,31,35) if (3<=x<=6 or 10<=x<=13) and 7<=y<=11 else (65,78,83)
 if name=='face_plain':return (84,105,108)
 if name=='scream':return (28,41,44) if 3<=x<=12 and 3<=y<=12 else (198,215,216)
 return _previous_texture_color(name,x,y)

def sculpt_silhouette(mesh,continuous_half=False):
 """Facet large volumes and taper their lower ends without changing the rig.

 Disjoint bands keep surfaces free of z-fighting. Every band inherits its
 source pivot, so armor, fur, hands and legs still follow the same poses.
 """
 import copy
 elements=[]
 for source in mesh['elements']:
  a,b=source['from'],source['to'];size=[b[i]-a[i] for i in range(3)]
  mat=next(iter(source['faces'].values()))['texture']
  eligible=mat in ('#fur','#fur_light','#fur_shadow','#steel','#mechanism','#metal_edge','#muzzle')
  # Preserve thin armor, facial panels, horns, teeth and all small details.
  inner_torso=continuous_half and source.get('name')=='torso_core'
  inner_skull=continuous_half and abs(size[1]-3.05)<1e-5 and abs(size[2]-3.7)<1e-5
  # Keep the two muzzle halves solid right up to their shared center seam.
  # Chamfering their seam-facing bands recessed the front and exposed the void.
  solid_muzzle=continuous_half and abs(size[1]-1.92)<1e-5 and abs(size[2]-1.67)<1e-5
  if solid_muzzle or inner_skull or inner_torso or not eligible or min(size)<1.35 or len({f['texture'] for f in source['faces'].values()})>1:
   elements.append(source);continue
  torso=size[0]>3 and size[1]>3 and a[1]>4 and (a[0]<8<b[0] or (size[1]>4.9 and size[2]>5.3))
  axis=1 if torso else 0
  cut=size[axis]*.22
  boundaries=[a[axis],a[axis]+cut,b[axis]-cut,b[axis]]
  for j in range(3):
   e=copy.deepcopy(source);e['from'][axis]=boundaries[j];e['to'][axis]=boundaries[j+1]
   seam_band=continuous_half and ((j==0 and 'west' not in source['faces']) or (j==2 and 'east' not in source['faces']))
   if axis==0 and j!=1 and not seam_band:
    # Chamfer shoulder, head and limb corners into a narrower outer facet.
    for k in (1,2):
     trim=min(.65,size[k]*.21)
     if k==1 and a[k]<1.3: # Keep grounded feet and knuckles at the same height.
      e['to'][k]-=trim*1.4
     else:e['from'][k]+=trim;e['to'][k]-=trim
   if axis==1:
    # A narrower waist flows into a broad middle chest and sloping mantle.
    trim=(.65 if j==0 else 0 if j==1 else .35)
    for k in (0,2):
     if not (continuous_half and k==0 and 'west' not in source['faces']):e['from'][k]+=trim
     if not (continuous_half and k==0 and 'east' not in source['faces']):e['to'][k]-=trim
   low,high=('west','east') if axis==0 else ('down','up')
   # Adjacent bands meet internally; only the exposed ledge remains.
   # Their cross sections differ, so retain the larger band's ledge face.
   if j>0 and axis==0 and j!=1:e['faces'].pop(low,None)
   if j<2 and axis==0 and j!=1:e['faces'].pop(high,None)
   if axis==1 and j==0:e['faces'].pop(high,None)
   if axis==1 and j==2:e['faces'].pop(low,None)
   elements.append(e)
  # Fur breaks up the lower edge of shoulder and cheek volumes.
  if not continuous_half and mat in ('#fur','#fur_light') and size[0]>2.1 and size[1]>2.5 and a[1]>6:
   for j in range(3):
    tuft=copy.deepcopy(source);x=a[0]+size[0]*(.16+.25*j);w=min(.6,size[0]*.16)
    tuft['from']=[x,a[1]-.35-(j%2)*.2,a[2]-.12]
    tuft['to']=[x+w,a[1]+.32,a[2]+.22]
    tuft['faces']={f:{'uv':[0,0,16,16],'texture':'#fur_shadow' if j%2 else '#fur_light'} for f in ('north','south','east','west','up','down')}
    elements.append(tuft)
 mesh['elements']=elements
 return mesh

_block_mother_model=mother_model

def model(frame=None,attack=None,kind='slam'):
 """Purpose-built natural gorilla anatomy with a horizontal trunk.

 All decorative parts share their limb pivot. A closed barrel joins the
 shoulders and hips; the forward fists and rear feet establish a knuckle stance.
 """
 es=[];phase=2*math.pi*(frame or 0)/24
 def box(a,b,mat,part=None,role=None,angle=0,pivot=None,axis='x',front=None):
  a=list(a);b=list(b)
  if part:
   side=-1 if part.endswith('l') else 1
   pivot=[8+side*4.5,10.3,7.2] if part.startswith('arm') else [8+side*1.7,3.0,10.4]
   if frame is not None:
    limb_phase=phase+(.25*side if kind=='gallop' else math.pi if side==1 else 0)
    if part.startswith('leg'):limb_phase+=math.pi*.65
    angle=round(math.sin(limb_phase)*(20 if kind=='gallop' else 12 if part.startswith('leg') else 10),6)
    lift=max(0,math.sin(limb_phase))*(.35 if part.startswith('leg') else .55)
    a[1]+=lift;b[1]+=lift
   if attack is not None and part.startswith('arm'):
    peak=round(math.sin(math.pi*attack/7)*2)*22.5
    angle=peak if kind=='slam' else -peak
    if (kind=='swipe' and side==1) or (kind=='throw' and side==-1):angle=0
    if kind=='roar':angle=22.5
    if kind=='whirl':angle=side*45*attack/7;axis='z'
  e={'from':a,'to':b,'faces':{f:{'uv':[0,0,16,16],'texture':'#'+mat} for f in ('north','south','east','west','up','down')}}
  if part:e['name']=part
  if role:e['role']=role
  if front:e['faces']['north']['texture']='#'+front
  if angle:e['rotation']={'origin':pivot,'angle':angle,'axis':axis,'rescale':False}
  if mat=='reactor':e['light_emission']=12
  es.append(e);return e
 def half(a,b,mat,metal='steel',role=None):
  # Closed halves meet at the internal seam. Only their internal faces are omitted.
  l=box(a,(8,b[1],b[2]),mat,role=role);r=box((8,a[1],a[2]),b,metal,role=role)
  l['faces'].pop('east');r['faces'].pop('west')
  if role in ('torso_core','skull_core'):l['name']=r['name']=role
 # Short, bent rear legs and broad feet hold the weight of the hunched body.
 for side in (-1,1):
  part='leg_l' if side<0 else 'leg_r';x=4.55 if side<0 else 8.95
  organic=side<0
  box((x,1.3,8.65),(x+2.5,3.3,12.45),'fur' if organic else 'steel',part,role='thigh')
  box((x+.12,.55,9.1),(x+2.34,1.8,12.7),'fur_shadow' if organic else 'metal_edge',part,role='shin')
  box((x-.23,0,7.65),(x+2.72,.83,13.05),'fur_light' if organic else 'steel',part,role='foot')
  if not organic:
   box((x+.62,.9,8.94),(x+1.82,1.55,9.08),'mechanism',part)
   box((x+.92,1.03,8.79),(x+1.48,1.43,8.93),'reactor',part)
 # Broad rounded shoulders, tapering upper arms, thick forward forearms.
 for side in (-1,1):
  part='arm_l' if side<0 else 'arm_r'
  def arm(a,b,mat,role=None):
   if side>0:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   return box(a,b,mat if side<0 else {'fur':'steel','fur_light':'steel','fur_shadow':'metal_edge'}.get(mat,mat),part,role)
  arm((.45,8.1,4.2),(4.25,11.55,10.65),'fur_light','shoulder')
  arm((1.05,10.9,5.15),(3.9,12.25,9.7),'fur','shoulder_crown')
  arm((.85,5.2,3.9),(3.95,8.75,9.4),'fur','upper_arm')
  arm((.3,1.5,1.72),(4.02,5.8,7.28),'fur_light','forearm')
  if side>0:
   # Keep the existing mechanical hand exactly as designed.
   arm((.18,0,.6),(4.27,2.05,6.2),'fur_shadow','fist')
   for j in range(3):
    x=.32+j*1.24
    arm((x,.28,.27),(x+1.07,1.62,.59),'fur_light','knuckle')
   arm((3.72,.65,1.32),(4.55,2.65,3.15),'fur','thumb')
  else:
   # A fleshy palm with four individually curled fingers and an opposed thumb.
   # Each finger's two joints overlap the palm and the next phalanx.
   arm((.25,.85,2.1),(3.95,2.1,5.8),'fur_shadow','fist')
   arm((.45,1.15,2.55),(3.73,1.69,5.45),'fur_light','hand_fur')
   for j in range(4):
    x=.38+j*.82;rise=(.1 if j in (1,2) else 0)
    arm((x,1.0,.96),(x+.66,1.68+rise,2.38),'fur_light','knuckle')
    arm((x+.03,0,.58),(x+.63,1.1+rise,1.42),'fur_shadow','finger')
    arm((x+.08,.12,1.3),(x+.59,.58+rise,2.25),'fur','fingertip')
   arm((3.5,1.35,3.34),(4.25,2.62,4.9),'fur','thumb')
   arm((3.83,.72,2.81),(4.42,1.75,3.88),'fur_shadow','thumb_tip')
 # Long layered fur follows the organic shoulder and elbow, tapering in length.
 for j in range(5):
  x=.55+j*.65
  box((x,7.15+(j%2)*.25,3.92),(x+.52,10.6-abs(j-2)*.22,4.18),'fur_light','arm_l',role='shoulder_fur')
  box((x+.08,6.7+(j%2)*.25,4.02),(x+.42,7.7+(j%2)*.15,4.28),'fur_shadow','arm_l')
 for j in range(3):
  x=.72+j*.92
  box((x,2.18,1.38),(x+.72,4.72-j*.12,1.69),'fur','arm_l',role='forearm_fur')
 # Machinery is integrated into the thick arm, not a cage of floating rails.
 box((12.18,2.25,1.31),(12.55,5.45,1.69),'metal_edge','arm_r',role='piston')
 box((14.92,2.28,1.29),(15.3,5.39,1.67),'metal_edge','arm_r',role='piston_outer')
 box((12.81,2.51,1.39),(14.51,4.95,1.7),'mechanism','arm_r',role='forearm_motor')
 box((13.34,2.98,1.2),(13.93,4.47,1.38),'reactor','arm_r')
 box((12.34,7.4,3.57),(14.91,8.15,3.88),'metal_edge','arm_r')
 box((12.39,9.0,3.91),(15.15,10.75,4.17),'metal_edge','arm_r',role='shoulder_plate')
 box((15.57,6.12,4.42),(15.78,9.25,4.8),'cable','arm_r')
 for j in range(4):
  x=12.52+j*.63
  box((x,9.35,3.70),(x+.39,10.42,3.9),'mechanism','arm_r')
  box((x+.08,9.55,3.54),(x+.27,10.2,3.69),'reactor','arm_r')
 # Head sits below the shoulder crowns and well ahead of the high rear hump.
 half((5.15,8.5,2.25),(10.85,11.65,6.65),'fur',role='skull_core')
 half((5.6,11.1,2.0),(10.4,11.95,5.8),'fur_light',role='crown')
 box((5.56,9.35,1.86),(10.44,11.25,2.23),'face_plain',role='face')
 # Heavy diagonal brows narrow the eyes into an aggressive stare.
 box((5.7,10.75,1.5),(7.85,11.3,1.85),'fur_shadow',role='brow_l',angle=-22.5,pivot=[7.6,10.95,1.7],axis='z')
 box((8.15,10.75,1.49),(10.3,11.3,1.84),'metal_edge',role='brow_r',angle=22.5,pivot=[8.4,10.95,1.7],axis='z')
 box((6.1,10.23,1.6),(7.35,10.65,1.85),'face_plain',role='eye_l',front='ice_face')
 box((8.65,10.23,1.6),(9.9,10.65,1.85),'metal_edge',role='eye_r',front='optic')
 half((5.8,8.7,1.04),(10.2,10.13,2.5),'muzzle',role='muzzle')
 box((6.62,9.49,.69),(9.38,10.14,1.03),'nose',role='nose')
 # Dark lower jaw and cheek framing avoid the previous rectangular face panel.
 half((6.1,8.35,1.37),(9.9,8.77,3.1),'fur_shadow',role='jaw')
 box((5.02,8.82,2.01),(5.57,10.85,3.8),'fur_light',role='cheek_l')
 box((10.43,8.83,2.02),(10.98,10.86,3.81),'steel',role='cheek_r')
 if kind=='roar' and attack is not None:
  box((6.15,8.04,1.01),(9.85,8.64,1.36),'face_plain',role='mouth',front='scream')
  for j in range(7):
   x=6.26+j*.5
   box((x,8.37,.94),(x+.28,8.59,1.0),'tooth',role='tooth')
 # Swept branching horns retain connected joints, emerging from the skull sides.
 for side in (-1,1):
  def beam(start,length,vertical=False,angle=-22.5,width=.62):
   radians=math.radians(angle)
   direction=(-math.sin(radians),math.cos(radians)) if vertical else (-math.cos(radians),-math.sin(radians))
   end=(start[0]+direction[0]*length,start[1]+direction[1]*length)
   center=[(start[0]+end[0])/2,(start[1]+end[1])/2,4.65]
   halfsize=[width/2,(length+.28)/2] if vertical else [(length+.28)/2,width/2]
   a=(center[0]-halfsize[0],center[1]-halfsize[1],4.25);b=(center[0]+halfsize[0],center[1]+halfsize[1],5.05)
   if side>0:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2]);center[0]=16-center[0]
   box(a,b,'horn',role='antler',angle=angle if side<0 else -angle,pivot=center,axis='z')
   return end
  joint=beam((5.32,11.5),1.8)
  tip=beam(joint,1.65,width=.55)
  beam(tip,1.5,vertical=True,angle=22.5,width=.46)
  beam(joint,1.1,vertical=True,angle=-22.5,width=.48)
  beam((joint[0]+.35,joint[1]-.15),.95,vertical=True,angle=22.5,width=.45)
 # Closed stepped caps soften the shoulder and forearm silhouette. Each band
 # keeps every exterior face and the same pivot; no open shell or hidden core.
 import copy
 shaped=[]
 for e in es:
  if e.get('role') not in ('shoulder','forearm'):
   shaped.append(e);continue
  a,b=e['from'],e['to'];height=b[1]-a[1]
  cuts=[a[1],a[1]+height*.2,b[1]-height*.2,b[1]]
  for j in range(3):
   band=copy.deepcopy(e);band['from'][1]=cuts[j];band['to'][1]=cuts[j+1]
   if j!=1:
    trim=.28 if e['role']=='shoulder' else .18
    for axis in (0,2):band['from'][axis]+=trim;band['to'][axis]-=trim
   shaped.append(band)
 es=shaped
 for e in es:
  limb=e.get('name','')
  center=2.1 if limb=='arm_l' else 13.9 if limb=='arm_r' else None
  for bound in ('from','to'):
   e[bound][1]=round(13.11+(e[bound][1]-11.5)*.75 if e.get('role')=='antler' else e[bound][1]*1.14,8)
   if center is not None:e[bound][0]=round(center+(e[bound][0]-center)*.62,8)
   e[bound][0]=round(8+(e[bound][0]-8)*.75,8)
   e[bound][2]=round(7+(e[bound][2]-7)*.78,8)
  if 'rotation' in e:
   origin=e['rotation']['origin'];origin[1]=round(13.11+(origin[1]-11.5)*.75 if e.get('role')=='antler' else origin[1]*1.14,8)
   if center is not None:origin[0]=round(center+(origin[0]-center)*.62,8)
   origin[0]=round(8+(origin[0]-8)*.75,8)
   origin[2]=round(7+(origin[2]-7)*.78,8)
 # A natural quadrupedal layout, rebuilt in native model coordinates.
 # Retain the facial and hand designs, replacing every old torso volume.
 head_roles={'skull_core','crown','face','brow_l','brow_r','eye_l','eye_r','muzzle','nose','jaw','cheek_l','cheek_r','mouth','tooth','antler'}
 hand_roles={'fist','hand_fur','knuckle','finger','fingertip','thumb','thumb_tip'}
 es=[e for e in es if e.get('name','').startswith(('arm','leg')) or e.get('role') in head_roles]
 for e in es:
  limb=e.get('name','');role=e.get('role')
  if limb.startswith('arm'):
   for bound in ('from','to'):
    e[bound][2]=round(e[bound][2]-1,8)
    if role not in hand_roles:e[bound][1]=round(e[bound][1]*.72+.012,8)
   if 'rotation' in e:
    origin=e['rotation']['origin'];origin[1]=round(origin[1]*.72+.012,8);origin[2]=round(origin[2]-1,8)
  elif limb.startswith('leg'):
   side=-1 if limb.endswith('l') else 1
   lift=e['from'][1]-(1.482 if role=='thigh' else .627 if role=='shin' else 0)
   if role=='thigh':
    e['from'][1:]=[3+lift,9.45];e['to'][1:]=[6.2+lift,12.0]
   elif role=='shin':
    e['from'][1:]=[1+lift,9.55];e['to'][1:]=[3.3+lift,12.4]
   elif role=='foot':
    e['from'][2]=9.4;e['to'][2]=13.5
   else:
    for bound in ('from','to'):e[bound][1]+= .6;e[bound][2]+= .97
   rotation=e.get('rotation')
   if role=='thigh':rotation=e.setdefault('rotation',{'angle':0,'axis':'x','rescale':False});rotation['angle']=round(rotation['angle']+22.5,6)
   if rotation:rotation['origin']=[8+side*1.275,5.8,11.4]
  else:
   for bound in ('from','to'):
    e[bound][1]=round(e[bound][1]-4,8);e[bound][2]=round(e[bound][2]-.7,8)
   if 'rotation' in e:
    origin=e['rotation']['origin'];origin[1]=round(origin[1]-4,8);origin[2]=round(origin[2]-.7,8)
 # Long closed trunk from the forward shoulder cage to the rear pelvis.
 half((5.35,4.6,4.4),(10.65,8.9,11.6),'fur_shadow',role='torso_core')
 half((5.05,5.5,4.85),(10.95,9.35,9.45),'fur',role='ribcage')
 half((4.45,7.2,4.75),(11.55,10.05,8.4),'fur_light',role='mantle')
 half((5.3,8.3,6.5),(10.7,10.4,9.65),'fur_shadow',role='silverback_hump')
 half((5.9,9.7,7.1),(10.1,10.75,9.3),'fur_light',role='hump_crown')
 half((5.7,4.2,9.65),(10.3,7.55,12.4),'fur',role='hips')
 half((5.9,6.3,9.3),(10.1,8.6,11.9),'fur_shadow',role='rump')
 box((5.2,5.8,4.05),(7.98,8.45,5.0),'fur_light',role='pectoral_l')
 box((8.02,5.8,4.02),(10.8,8.45,4.97),'steel',role='pectoral_r')
 half((5.8,4.45,6.1),(10.2,6.05,10.75),'fur',role='abdomen')
 box((8.45,6.3,3.85),(10.1,8.0,4.01),'metal_edge',role='reactor_socket')
 box((8.7,6.55,3.66),(9.85,7.75,3.84),'reactor',role='chest_reactor')
 for j in range(3):
  box((10.18,6.4+j*.48,3.9),(10.8,6.61+j*.48,4.015),'mechanism')
  box((10.25,6.46+j*.48,3.74),(10.64,6.55+j*.48,3.89),'reactor')
 for j in range(3):
  x=5.45+j*.73
  box((x,5.3-(j%2)*.15,3.94),(x+.53,6.1,4.045),'fur_light',role='chest_fur')
 if frame is not None:
  sway=.12*math.sin(phase);bob=(.22 if kind=='gallop' else .08)*(1-math.cos(2*phase))
  for e in es:
   for bound in ('from','to'):e[bound][0]+=sway;e[bound][1]+=bob
   if 'rotation' in e:e['rotation']['origin'][0]+=sway;e['rotation']['origin'][1]+=bob
 return {'elements':es,'textures':{n:'yetiboss:boss/father_'+n for n in (*BASE_MATERIALS,*CYBORG_MATERIALS)},
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}

def mother_model(frame=None,attack=None,kind='slam'):
 return sculpt_silhouette(_block_mother_model(frame,attack,kind))

# Keep the approved procedural model available as a conversion reference.
procedural_father_model=model
from imported_father import model as model, TEXTURE_BYTES as IMPORTED_FATHER_TEXTURES
COLORS.update({name:(0,0,0,255) for name in IMPORTED_FATHER_TEXTURES})
