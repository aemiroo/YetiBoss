"""Original ice-armored sentinel, with distance-driven walking poses."""
import math
from boss_model import COLORS
MATERIALS={'warden_ice':(92,174,207,255),'warden_dark':(24,57,79,255),'warden_edge':(187,237,249,255),'warden_core':(108,255,244,255)}
COLORS.update(MATERIALS)
def texture_color(name,x,y):
 c=MATERIALS[name][:3]
 if name=='warden_core':return c
 seam=(x+2*y)%13==0 or (2*x-y)%19==0
 delta=24 if seam else (-9 if (x//3+y//4)%3==0 else 0)
 return tuple(max(0,min(255,v+delta)) for v in c)
def model(frame=None,kind="walk"):
 es=[];phase=2*math.pi*(frame or 0)/24
 def box(a,b,mat,limb=None):
  e={'from':list(a),'to':list(b),'faces':{side:{'texture':'#'+mat,'uv':[0,0,16,16]} for side in ('north','south','east','west','up','down')}}
  if mat=='warden_core':e['light_emission']=15
  if limb and frame is not None and kind=="walk":
   left=limb.endswith('l');angle=math.sin(phase+(0 if left else math.pi))*(12 if limb.startswith('leg') else -15)
   e['rotation']={'origin':[5 if left else 11,4.5 if limb.startswith('leg') else 10,8],'axis':'x','angle':angle,'rescale':False}
  if limb and limb.startswith('arm') and kind in ('strike','roar','sniff'):
   left=limb.endswith('l')
   angles={'strike':(45,42,34,22,8,-8,-15,-12,-8,-4,-1,0),'roar':(0,12,25,38,38,25,12,0),'sniff':(0,8,16,22,22,16,8,0)}
   e['rotation']={'origin':[5 if left else 11,10,8],'axis':'x','angle':angles[kind][frame or 0],'rescale':False}
  if kind=='hurt':
   shift=(0,-.12,-.22,-.17,-.10,-.04,0,0)[frame or 0]
   e['from'][2]+=shift;e['to'][2]+=shift
  elif kind=='emerge':
   shift=-12*(1-(frame or 0)/7)**2
   e['from'][1]+=shift;e['to'][1]+=shift
  elif kind=='idle' and (not limb or not limb.startswith('leg')):
   breath=.08*(1-math.cos(2*math.pi*(frame or 0)/8))
   e['from'][1]+=breath;e['to'][1]+=breath
  es.append(e)
 box((4,4.5,5.5),(12,11.8,10.5),'warden_dark')
 box((4.3,5,5.1),(7.2,11.3,5.5),'warden_ice');box((8.8,5,5.1),(11.7,11.3,5.5),'warden_ice')
 box((7.2,7.6,5.05),(8.8,10.2,5.5),'warden_core')
 box((6,11.8,6),(10,14,10),'warden_ice')
 box((6.4,12.25,5.8),(9.6,13.3,6),'warden_dark')
 box((6.65,12.6,5.65),(9.35,12.95,5.8),'warden_core')
 for side in ('l','r'):
  x=0 if side=='l' else 10
  box((x+1,9.7,5),(x+5,12,11),'warden_ice','arm_'+side)
  for i in range(3):
   shard=x+1.3+i
   box((shard,12,7),(shard+.7,13.3+(1-i)*.35,8.5),'warden_edge','arm_'+side)
  box((x+1.7,4.7,6),(x+4.3,9.7,10),'warden_dark','arm_'+side)
  box((x+1.3,3.7,5.5),(x+4.7,7.4,10.5),'warden_ice','arm_'+side)
  box((x+1.5,3.1,5.2),(x+4.5,4.2,9.7),'warden_edge','arm_'+side)
  leg=4 if side=='l' else 9
  box((leg,0,6),(leg+3,4.5,10),'warden_ice','leg_'+side)
  box((leg+.25,0,5.4),(leg+2.75,1.4,6),'warden_edge','leg_'+side)
  horn=4.8 if side=='l' else 10
  box((horn,12.1,7),(horn+1.2,14.8,8.8),'warden_edge')
  box((horn+.2,14.8,7.3),(horn+1,16,8.5),'warden_core')
 return {'elements':es,'textures':{n:'yetiboss:boss/'+n for n in MATERIALS},'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}
