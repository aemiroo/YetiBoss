"""Stocky glacier Yeti preview, built from shaped cuboids."""
import math
COLORS={'fur':(214,231,239,255),'fur_light':(243,250,253,255),'fur_shadow':(167,194,209,255),
 'ice':(65,187,223,255),'ice_dark':(35,116,156,255),'ice_light':(140,232,247,255),
 'ice_face':(64,190,222,255)}
COLORS['muzzle']=(61,86,97,255)
COLORS['scream']=(61,86,97,255)
COLORS['tooth']=(231,235,216,255)
COLORS.update({'horn':(54,70,82,255),'nose':(78,89,100,255)})
def texture_color(mat,x,y):
 if mat=='tooth':return COLORS[mat][:3]
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

def model(frame=None,attack=None,kind='slam'):
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
 box((4.8,4.1,6),(11.2,6,10.8),'fur_shadow')
 for x,part in ((4.8,'leg_l'),(8.8,'leg_r')):
  box((x,1,6.6),(x+2.4,4.7,10.2),'fur',part)
  box((x,0,5.7),(x+2.4,1.2,10.3),'fur_shadow',part)
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
 box((5.6,10,3.95),(10.4,11.4,4.25),'ice_face')
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
  horn((4.4,12,6),(5.6,13,7.5))
 return {'elements':es,'textures':{n:'yetiboss:boss/'+n for n in COLORS},
         'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
