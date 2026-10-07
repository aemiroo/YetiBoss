"""Articulated cuboid reconstruction of the supplied mountain gorilla Yeti reference."""
import math
COLORS={'fur':(218,230,234,255),'fur_light':(239,245,246,255),'fur_shadow':(167,188,197,255),
 'frost':(190,218,228,255),'frost_dark':(91,118,129,255),'frost_light':(219,240,245,255),
 'face':(78,104,116,255),'mouth':(39,15,24,255),'tongue':(134,46,58,255),
 'tooth':(228,249,253,255),'eye':(250,38,36,255),'eye_shadow':(100,27,35,255)}
DIRECTIONS=('north','south','east','west','up','down')
def model(frame=None,attack=None):
 elements=[]
 phase=math.sin(2*math.pi*(frame or 0)/12)
 lift=round((-45*math.sin(math.pi*attack/7) if attack is not None else 0)/22.5)*22.5
 def box(a,b,mat,part='body',angle=0,pivot=None,axis='z'):
  a=list(a);b=list(b)
  if part.startswith('arm'):
   # Both arms travel forward together; legs alternate. Rest angles remain intact.
   dz=phase*.5 if frame is not None else 0
   a[2]+=dz;b[2]+=dz
   if attack is not None:angle=lift;axis='x';pivot=[3.5 if part=='arm_l' else 12.5,10.5,8]
  elif part.startswith('leg') and frame is not None:
   dz=phase*.65*(1 if part=='leg_l' else -1)
   a[2]+=dz;b[2]+=dz
  e={'from':a,'to':b,'faces':{face:{'uv':[0,0,16,16],'texture':'#'+mat} for face in DIRECTIONS}}
  if angle:e['rotation']={'origin':pivot,'axis':axis,'angle':angle,'rescale':False}
  elements.append(e)
 # Long tapered torso, wide upper chest and dark recessed pectorals.
 box((5,4.6,7),(11,8.5,11.7),'fur')
 box((4.4,8,6.5),(11.6,11.5,11.6),'fur')
 box((4.7,8.6,6.05),(7.8,10.9,6.5),'fur_shadow')
 box((8.2,8.6,6.05),(11.3,10.9,6.5),'fur_shadow')
 box((5.5,5.6,6.65),(10.5,8.4,7),'fur_shadow')
 # Sloping shoulders and angled two-section arms, rather than vertical slabs.
 for side,part in ((-1,'arm_l'),(1,'arm_r')):
  def mirror(a,b):
   return (a,b) if side<0 else ((16-b[0],a[1],a[2]),(16-a[0],b[1],b[2]))
  def limb(a,b,mat,angle,pivot):
   aa,bb=mirror(a,b);pp=[pivot[0] if side<0 else 16-pivot[0],pivot[1],pivot[2]]
   box(aa,bb,mat,part,angle*(-side),pp)
  limb((2.2,7,6.1),(4.7,11.3,10.7),'fur',-22.5,[3.7,10.7,8.4])
  limb((1.2,3.5,5.3),(3.8,7.9,10.2),'fur_light',-22.5,[2.6,7.5,7.8])
  limb((.8,2.5,4.9),(3.7,4.5,9),'face',-22.5,[2.2,4,7])
  # Four individually segmented bent fingers, with pointed icy tips.
  for index in range(4):
   x=.85+index*.68
   limb((x,1.7,4.4),(x+.5,3.2,5.3),'frost_dark',-22.5,[2.2,4,7])
   limb((x,1.45,3.95),(x+.45,2.1,4.5),'face',-22.5,[2.2,4,7])
   limb((x+.08,1.35,3.55),(x+.35,1.9,4.05),'tooth',-22.5,[2.2,4,7])
  limb((3.4,2.5,5.6),(4.2,3.8,6.8),'face',22.5,[3.5,3.8,6])
  # Overlapping tufts along the forward-facing forearms and shoulders.
  for n,y in enumerate((5,6.4,8,9.5)):
   x=1.4 if y<8 else 2.5
   limb((x,y,5.15),(x+.5,y+1.1,5.5),'fur_light',-22.5,[2.6,y+1,7.8])
  # Layered angled fur patches break up the arm outline.
  for y in (9,7,5):
   limb((1.1 if y<8 else 2,y,6),(1.7 if y<8 else 2.6,y+1.7,8.7),'frost' if y==5 else 'fur_shadow',-22.5,[2.6,y+1.5,8])
 # Long sturdy legs, bent outwards with substantial planted feet.
 box((5.2,1.1,7),(7.5,5.8,10.6),'fur','leg_l',-22.5,[6.5,5.5,8.5])
 box((8.5,1.1,7),(10.8,5.8,10.6),'fur','leg_r',22.5,[9.5,5.5,8.5])
 box((4.2,0,5.5),(7.1,1.5,10.7),'fur_shadow','leg_l')
 box((8.9,0,5.5),(11.8,1.5,10.7),'fur_shadow','leg_r')
 for x in (4.4,5.4,6.4,9.1,10.1,11.1):
  box((x,0,5.1),(x+.45,.65,5.7),'tooth','leg_l' if x<8 else 'leg_r')
 # Uneven chest fringe and abdominal fur, avoiding a smooth plate-like chest.
 for x,y in ((5,8),(6.2,7.8),(7.4,8.1),(8.6,7.7),(9.8,8)):
  box((x,y,6.1),(x+.45,y+.8,6.6),'fur_light')
 head_start=len(elements)
 # Smaller head. Hollow opening assembled from cheek walls, roof, jaw and back.
 box((5.6,12.4,5.2),(10.4,15.6,9.7),'fur')
 box((5.6,9.5,7.8),(10.4,12.4,9.7),'fur_shadow')
 box((5.6,9.5,4.65),(6.35,12.5,7.8),'fur_light')
 box((9.65,9.5,4.65),(10.4,12.5,7.8),'fur_light')
 box((6.35,9.6,7.65),(9.65,12.5,7.8),'mouth')
 box((6.2,9.15,4.6),(9.8,9.65,7.8),'face')
 box((6.5,9.65,6),(9.5,9.9,7.65),'tongue')
 box((6.2,12.25,4.5),(9.8,12.8,7.8),'face')
 # Muzzle above the mouth; small nostrils, deeply inset eyes and diagonal brows.
 box((6.8,12.65,4.45),(9.2,13.3,5.5),'face')
 for x in (7,8.65):box((x,12.9,4.35),(x+.35,13.2,4.5),'mouth')
 box((5.9,13.3,4.85),(7.4,14.2,5.2),'eye_shadow')
 box((8.6,13.3,4.85),(10.1,14.2,5.2),'eye_shadow')
 box((6.2,13.55,4.7),(7.1,13.95,4.9),'eye')
 box((8.9,13.55,4.7),(9.8,13.95,4.9),'eye')
 box((5.75,14.05,4.55),(7.55,14.55,5.5),'fur_light',angle=-22.5,pivot=[7.4,14.3,5])
 box((8.45,14.05,4.55),(10.25,14.55,5.5),'fur_light',angle=22.5,pivot=[8.6,14.3,5])
 # Long outer fangs and shorter teeth, tapered using a narrow second section.
 for x,length in ((6.4,1.8),(7.2,.55),(7.9,.6),(8.6,.55),(9.3,1.8)):
  box((x,12.3-length,4.6),(x+.35,12.3,5.05),'tooth')
  box((x+.08,12.1-length,4.65),(x+.26,12.3-length,4.95),'tooth')
 for x in (6.55,7.25,7.95,8.65,9.35):box((x,9.65,4.65),(x+.28,10.15,5),'tooth')
 # Jagged skull fur and jaw fringe. Short spiky crown, no smooth cuboid cap.
 for x,y in ((5.8,15.5),(6.5,15.8),(7.4,15.6),(8.6,15.7),(9.6,15.5)):
  box((x,y-.4,6),(x+.45,min(16,y+.2),8.8),'fur_light')
 for x in (5.35,10.25):
  box((x,11,5.7),(x+.4,14.5,7),'fur_shadow')
  box((x,10.7,5.7),(x+.25,11.4,6.5),'fur_light')
 for x in (6.4,7.2,8,8.8,9.4):
  box((x,8.7,5.9),(x+.3,9.4,6.9),'fur_light')
 # Keep the recessed mouth ahead of the chest instead of burying its back wall in the torso.
 for e in elements[head_start:]:
  e['from'][2]-=2;e['to'][2]-=2
  if 'rotation' in e:e['rotation']['origin'][2]-=2
 return {'credit':'Reference-based mountain Yeti reconstruction; original geometry and textures.',
         'textures':{name:'yetiboss:boss/'+name for name in COLORS},'elements':elements,
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
