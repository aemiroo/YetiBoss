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
 box((4.3,4.6,6.3),(11.7,10.7,11.8),'fur')
 box((4.2,9,8.3),(11.8,12,12.5),'fur_light',angle=22.5,pivot=[8,10,9],axis='x')
 box((4.82,4.1,6),(11.18,6,10.8),'fur_shadow')
 for x,part in ((4.8,'leg_l'),(8.8,'leg_r')):
  box((x,1,6.6),(x+2.4,4.7,10.2),'fur',part)
  box((x-.02,0,5.7),(x+2.42,1.2,10.3),'fur_shadow',part)
 for right in (False,True):
  part='arm_r' if right else 'arm_l'
  def arm(a,b,mat):
   if right:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   box(a,b,mat,part)
  arm((.9,7.8,6),(4.3,11.1,10.8),'fur_light')
  arm((1.55,4.3,6.4),(3.8,7.8,10.2),'fur')
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
   delta=26 if x in (1,14) or y in (1,14) else -14 if x in (3,12) or y in (3,12) else ((x//4+y//4)%3-1)*5
  elif name=='metal_edge':delta=18 if x<5 else -15 if x>12 else 0
  else:delta=((x//2+y//2)%3-1)*7
  return tuple(max(0,min(255,v+delta)) for v in c)
 if name in ('fur','fur_light','fur_shadow','horn','muzzle'):
  base={'fur':(226,234,232),'fur_light':(238,242,235),'fur_shadow':(198,215,216),'horn':(207,219,207),'muzzle':(220,229,227)}[name]
  patch=((x//3)*7+(y//3)*11+(x//3)*(y//3))%9
  delta=(-10,-5,0,0,0,3,5,7,9)[patch]
  return tuple(max(0,min(255,c+delta)) for c in base)
 if name=='ice_face':
  return (255,156,76) if 3<=x<=12 and 5<=y<=10 else (37,53,56)
 if name=='face_plain':return (84,105,108)
 if name=='scream':return (28,41,44) if 3<=x<=12 and 3<=y<=12 else (198,215,216)
 return _previous_texture_color(name,x,y)

def model(frame=None,attack=None,kind='slam'):
 """Antlered Father with forward shoulders and a low knuckle stance."""
 es=[];phase=2*math.pi*(frame or 0)/24
 def box(a,b,mat,part=None,angle=0,pivot=None,axis='x'):
  if part:
   side=-1 if part.endswith('l') else 1
   pivot=[8+side*4.5,10.3,7.2] if part.startswith('arm') else [8+side*1.7,4.4,8.5]
   if frame is not None:
    limb_phase=phase+(.25*side if kind=='gallop' else math.pi if side==1 else 0)
    if part.startswith('leg'):limb_phase+=math.pi*.65
    angle=round(math.sin(limb_phase)*(20 if kind=='gallop' else 12 if part.startswith('leg') else 10),6)
    lift=max(0,math.sin(limb_phase))*(.45 if part.startswith('leg') else .65)
    a=(a[0],a[1]+lift,a[2]);b=(b[0],b[1]+lift,b[2])
   if attack is not None and part.startswith('arm'):
    peak=round(math.sin(math.pi*attack/7)*2)*22.5
    angle=peak if kind=='slam' else -peak
    if kind=='swipe' and side==1:angle=0
    if kind=='throw' and side==-1:angle=0
    if kind=='roar':angle=22.5
  e={'from':list(a),'to':list(b),'faces':{f:{'uv':[0,0,16,16],'texture':'#'+mat} for f in ('north','south','east','west','up','down')}}
  if angle:e['rotation']={'origin':pivot,'angle':angle,'axis':axis,'rescale':False}
  es.append(e);return e
 # Deep shoulder mantle, low hips and a head recessed into the chest.
 box((3.6,6.5,6.4),(12.4,11.5,11.8),'fur',angle=22.5,pivot=[8,6.5,8])
 box((4.2,10.35,6.2),(11.8,12.6,10.9),'fur_light')
 box((5.5,4.2,7.0),(10.5,6.48,10.8),'fur_shadow')
 box((6.3,3.65,6.7),(9.7,4.18,10.5),'fur')
 for side in (-1,1):
  part='leg_l' if side==-1 else 'leg_r';x=5.2 if side==-1 else 8.6
  box((x,2.45,8.05),(x+2.2,4.25,11.0),'fur',part)
  box((x,1.0,7.2),(x+2.2,2.42,10.35),'fur_shadow',part)
  box((x-.15,0,6.3),(x+2.35,1.03,10.7),'fur_light',part)
  part='arm_l' if side==-1 else 'arm_r'
  def arm(a,b,mat):
   if side==1:a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2])
   return box(a,b,mat,part)
  arm((.8,6.6,5.7),(3.58,10.9,10.4),'fur_light')
  arm((1.35,2.6,4.8),(3.55,6.58,8.8),'fur')
  arm((.85,0.1,3.6),(3.85,2.63,8.9),'fur_shadow')
  # Light cuff and subtly striped oversized fist.
  arm((.79,2.5,3.54),(3.91,3.1,8.96),'fur_light')
 head_start=len(es)
 box((5.25,10.3,4.8),(10.75,13.4,8.0),'fur_light')
 face=box((5.85,11.15,4.49),(10.15,12.95,4.78),'face_plain')
 face['faces']['north']['texture']='#face_plain'
 # Wide projecting muzzle conceals the lower face, rather than a small nose.
 box((5.35,9.25,2.8),(10.65,11.17,4.47),'muzzle')
 if kind=='roar' and attack is not None:
  mouth=box((6.0,8.9,2.75),(10.0,9.23,3.9),'face_plain')
  mouth['faces']['north']['texture']='#scream'
  for x in (6.15,6.7,7.25,7.8,8.35,8.9,9.45):
   box((x,9.0,2.69),(x+.28,9.215,2.74),'tooth')
 # Pale blue fringe beneath the square muzzle.
 for j,x in enumerate((6.1,7.2,8.3,9.4)):
  box((x,8.55-(j%2)*.25,3.5),(x+.65,9.21,4.25),'fur_shadow')
 # Antlers use shared joint coordinates; extend each beam into its joint.
 # Rotating disconnected boxes about their own centers left floating tips.
 for side in (-1,1):
  def beam(start,length,vertical=False,angle=-22.5,width=.62):
   radians=math.radians(angle)
   direction=(-math.sin(radians),math.cos(radians)) if vertical else (-math.cos(radians),-math.sin(radians))
   end=(start[0]+direction[0]*length,start[1]+direction[1]*length)
   center=[(start[0]+end[0])/2,(start[1]+end[1])/2,6.02]
   half=[width/2,(length+.28)/2] if vertical else [(length+.28)/2,width/2]
   a=(center[0]-half[0],center[1]-half[1],5.62)
   b=(center[0]+half[0],center[1]+half[1],6.42)
   if side==1:
    a,b=(16-b[0],a[1],a[2]),(16-a[0],b[1],b[2]);center[0]=16-center[0]
   box(a,b,'horn',angle=angle if side==-1 else -angle,pivot=center,axis='z')
   return end
  root=(5.32,12.68)
  joint=beam(root,1.8)
  tip=beam(joint,1.65,width=.55)
  beam(tip,1.5,vertical=True,angle=22.5,width=.46)
  beam(joint,1.1,vertical=True,angle=-22.5,width=.48)
  beam((joint[0]+.35,joint[1]-.15),.95,vertical=True,angle=22.5,width=.45)
 # Lowered head and antlers sit forward of the shoulder mantle.
 for e in es[head_start:]:
  for bound in ('from','to'):
   e[bound][1]=round(e[bound][1]-1.1,6)
   e[bound][2]=round(e[bound][2]-.45,6)
  if 'rotation' in e:
   e['rotation']['origin'][1]-=1.1
   e['rotation']['origin'][2]-=.45
 # Solid skull backing closes the faceted seam and the brow-to-muzzle gap.
 box((5.8,9.1,3.90),(10.23,12.15,7.60),'fur')
 # Continuous inner torso joins hips to shoulders under the shaped outer shell.
 box((6.28,4.0,7.18),(9.72,11.25,10.62),'fur')
 # Replace the right half with metal, leaving the opposite half organic.
 import copy
 rebuilt=[]
 for e in es:
  mat=e['faces']['up']['texture'][1:]
  if mat not in ('fur','fur_light','fur_shadow','muzzle'):
   rebuilt.append(e);continue
  if e['to'][0]<=8:
   rebuilt.append(e);continue
  mechanical=e
  if e['from'][0]<8:
   organic=copy.deepcopy(e);organic['to'][0]=8
   mechanical=copy.deepcopy(e);mechanical['from'][0]=8
   # The seam is internal; do not draw opposing coplanar faces.
   organic['faces'].pop('east');mechanical['faces'].pop('west')
   rebuilt.append(organic)
  replacement={'fur':'steel','fur_light':'steel','fur_shadow':'metal_edge','muzzle':'steel'}[mat]
  for f in mechanical['faces'].values():f['texture']='#'+replacement
  rebuilt.append(mechanical)
 es=rebuilt
 # Exposed elbow/forearm pistons and finger armor follow the same shoulder rig.
 box((12.0,6.2,4.42),(15.25,7.12,5.67),'metal_edge','arm_r')
 box((12.18,3.2,4.08),(12.55,6.26,4.40),'metal_edge','arm_r')
 box((14.65,3.25,4.02),(15.03,6.21,4.39),'metal_edge','arm_r')
 box((12.80,3.15,4.32),(14.38,6.14,4.70),'mechanism','arm_r')
 box((13.31,3.7,4.10),(13.86,5.76,4.30),'reactor','arm_r')
 for j in range(3):
  x=12.28+j*.92
  box((x,.35,3.21),(x+.70,2.34,3.54),'steel','arm_r')
  box((x+.16,.68,3.05),(x+.53,1.05,3.19),'metal_edge','arm_r')
 # A shoulder cap and external conduit leave the dark frame visible.
 box((12.1,9.7,5.33),(15.45,10.99,10.59),'steel','arm_r')
 box((15.46,7.44,6.1),(15.72,9.55,6.47),'cable','arm_r')
 # Half chest plate, reactor and exposed lower rib rails tilt with the torso.
 def chest(a,b,mat):return box(a,b,mat,angle=22.5,pivot=[8,6.5,8])
 chest((8.12,8.72,6.04),(12.15,10.22,6.34),'steel')
 chest((8.15,6.72,5.96),(11.88,8.66,6.29),'mechanism')
 chest((9.1,7.18,5.68),(10.76,8.44,5.94),'metal_edge')
 chest((9.35,7.38,5.49),(10.52,8.23,5.67),'reactor')
 for y in (6.91,7.42,7.93):chest((10.91,y,5.70),(11.65,y+.18,5.95),'metal_edge')
 chest((8.25,7.04,5.71),(8.57,8.51,5.95),'cable')
 # Organic eye shares the mechanical lens height, size and front plane.
 organic_eye=box((6.48,10.68,3.48),(7.30,11.18,3.58),'face_plain')
 organic_eye['faces']['north']['texture']='#ice_face'
 # Mechanical eye covers only one side of the recessed face.
 box((8.15,10.05,3.78),(10.2,11.89,4.025),'steel')
 box((8.53,10.55,3.59),(9.7,11.35,3.77),'mechanism')
 lens=box((8.70,10.68,3.48),(9.52,11.18,3.58),'steel')
 lens['faces']['north']['texture']='#optic'
 # Boot/shin plates finish the repaired mechanical half.
 box((8.91,1.2,6.81),(10.48,2.34,7.19),'steel','leg_r')
 box((9.42,1.38,6.60),(9.97,2.11,6.80),'reactor','leg_r')
 if frame is not None:
  sway=.18*math.sin(phase);bob=(.35 if kind=='gallop' else .12)*(1-math.cos(2*phase))
  for element in es:
   for bound in ('from','to'):
    element[bound][0]+=sway;element[bound][1]+=bob
   if 'rotation' in element:
    element['rotation']['origin'][0]+=sway;element['rotation']['origin'][1]+=bob
 return {'elements':es,'textures':{n:'yetiboss:boss/father_'+n for n in (*BASE_MATERIALS,*CYBORG_MATERIALS)},
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}


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
  inner_torso=continuous_half and abs(size[1]-7.25)<1e-5 and abs(size[2]-3.44)<1e-5
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
   if axis==0 and j!=1:
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

_block_father_model=model
_block_mother_model=mother_model
def model(frame=None,attack=None,kind='slam'):
 return sculpt_silhouette(_block_father_model(frame,attack,kind),continuous_half=True)
def mother_model(frame=None,attack=None,kind='slam'):
 return sculpt_silhouette(_block_mother_model(frame,attack,kind))
