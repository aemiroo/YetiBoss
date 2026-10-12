"""User GLB cuboids and UV patches, articulated through its original hierarchy.

 Sampling and export are standard-library only. Pose adaptation happens on
 source bones, never by deforming or approximating the supplied mesh volumes.
 """
import base64,bisect,copy,functools,json,math,pathlib
ROOT=pathlib.Path(__file__).parent/'imported/father'
DATA=json.loads((ROOT/'scene.json').read_text())
TEXTURE_BYTES={k:base64.b64decode(v) for k,v in json.loads((ROOT/'textures.json').read_text()).items()}
BONES={n['name']:i for i,n in enumerate(DATA['nodes'])}
UPPER=BONES['upperbody_84'];HEAD=BONES['h_head_61'];JAW=BONES['h_jaw_60']
LEFT=BONES['left_arm_72'];RIGHT=BONES['right_arm_83'];HAND=BONES['right_hand_81'];FOREARM=BONES['right_forearm_82']

def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def vec(a,v):return [sum(a[i][j]*v[j] for j in range(3)) for i in range(3)]
def add(a,b):return [x+y for x,y in zip(a,b)]
def identity():return [[1,0,0],[0,1,0],[0,0,1]]
def rotation(axis,angle):
 c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
 return [[1,0,0],[0,c,-s],[0,s,c]] if axis=='x' else [[c,0,s],[0,1,0],[-s,0,c]] if axis=='y' else [[c,-s,0],[s,c,0],[0,0,1]]
def quat(q):
 x,y,z,w=q;length=math.sqrt(sum(v*v for v in q));x,y,z,w=[v/length for v in q]
 return [[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
def angles(r):
 y=math.asin(max(-1,min(1,-r[2][0])))
 if abs(math.cos(y))>1e-7:x=math.atan2(r[2][1],r[2][2]);z=math.atan2(r[1][0],r[0][0])
 else:x=math.atan2(-r[1][2],r[1][1]);z=0
 return [math.degrees(v) for v in (x,y,z)]
def sample(channel,time):
 times=channel['times'];values=channel['values'];i=max(0,min(len(times)-2,bisect.bisect_right(times,time)-1))
 if len(times)==1:return values[0]
 f=max(0,min(1,(time-times[i])/max(1e-12,times[i+1]-times[i])))
 if channel['interpolation']=='STEP':return values[i]
 a=values[i];b=values[i+1]
 if channel['path']=='rotation':
  dot=sum(x*y for x,y in zip(a,b))
  if dot<0:b=[-v for v in b];dot=-dot
  if dot<.9995:
   theta=math.acos(max(-1,min(1,dot)));s=math.sin(theta)
   return [(math.sin((1-f)*theta)*x+math.sin(f*theta)*y)/s for x,y in zip(a,b)]
 return [(1-f)*x+f*y for x,y in zip(a,b)]

def transforms(clip,time,kind='idle',attack=None):
 values={}
 for channel in DATA['clips'][clip]['channels']:
  values.setdefault(channel['node'],{})[channel['path']]=sample(channel,time)
 worlds={}
 def walk(i,parent_r,parent_t):
  n=DATA['nodes'][i];v=values.get(i,{})
  t=list(v.get('translation',n.get('translation',[0,0,0])));r=quat(v.get('rotation',n.get('rotation',[0,0,0,1])));sc=list(v.get('scale',n.get('scale',[1,1,1])))
  if i==UPPER:r=mul(rotation('x',-40),r)
  if i in (HEAD,LEFT,RIGHT):r=mul(rotation('x',40),r)
  if i in (LEFT,RIGHT):sc=[s*.8 for s in sc]
  if kind=='whirl' and i in (LEFT,RIGHT):
   phase=(attack or 0)/7
   lift=48*math.sin(math.pi*phase)+7*math.sin(2*math.pi*phase)
   r=mul(rotation('z',(-1 if i==LEFT else 1)*lift),r)
  if kind=='roar' and i==JAW:r=mul(rotation('x',-25*math.sin(math.pi*(attack or 0)/7)),r)
  if kind=='roar' and i in (LEFT,RIGHT):r=mul(rotation('x',-15*math.sin(math.pi*(attack or 0)/7)),r)
  local=[[r[row][col]*sc[col] for col in range(3)] for row in range(3)]
  R=mul(parent_r,local);T=add(vec(parent_r,t),parent_t)
  if i==HEAD:T[1]-=.10;T[2]-=.18
  if i in (LEFT,RIGHT):T[1]-=.09
  worlds[i]=(R,T)
  for child in n.get('children',[]):walk(child,R,T)
 for root in DATA['roots']:walk(root,identity(),[0,0,0])
 return worlds

# Fixed normalization is shared by every pose: no bounding-box rescale per frame.
REST=transforms('idle',0)
rest_vertices=[]
for c in DATA['cubes']:
 R,T=REST[c['node']]
 for x in (c['from'][0],c['to'][0]):
  for y in (c['from'][1],c['to'][1]):
   for z in (c['from'][2],c['to'][2]):rest_vertices.append(add(vec(R,[x,y,z]),T))
LO=[min(v[k] for v in rest_vertices) for k in range(3)];HI=[max(v[k] for v in rest_vertices) for k in range(3)]
SCALE=13.2/max(HI[k]-LO[k] for k in range(3));OFFSET=[8-(LO[0]+HI[0])/2*SCALE,-LO[1]*SCALE,8-(LO[2]+HI[2])/2*SCALE]
def point(p):return [round(p[k]*SCALE+OFFSET[k],8) for k in range(3)]

def extras():
 result=[]
 def box(node,a,b,mat,role=None,front=None):
  c={'node':node,'from':a,'to':b,'faces':{s:mat for s in ('north','south','east','west','up','down')},'part':'head' if node==HEAD else 'arm_r' if node in (RIGHT,FOREARM,HAND) else 'torso','mechanical':True,'role':role,'source_name':'cyborg_'+str(len(result))}
  if front:c['faces']['north']=front
  if mat=='reactor':c['light_emission']=12
  result.append(c)
 box(UPPER,[.08,.15,-.48],[.45,.72,-.35],'metal_edge','reactor_socket')
 box(UPPER,[.16,.27,-.505],[.38,.58,-.47],'reactor','chest_reactor')
 for y in (.18,.38,.58):box(UPPER,[.46,y,-.49],[.58,y+.08,-.35],'reactor')
 box(FOREARM,[-.18,-.46,-.265],[.18,-.06,-.195],'mechanism','forearm_motor')
 box(FOREARM,[-.17,-.49,-.285],[-.125,-.01,-.18],'metal_edge','piston')
 box(FOREARM,[.18,-.49,-.285],[.225,-.01,-.18],'metal_edge','piston_outer')
 box(FOREARM,[-.04,-.43,-.295],[.05,-.12,-.26],'reactor')
 box(FOREARM,[.21,-.48,-.17],[.24,.01,-.12],'cable')
 box(RIGHT,[-.25,-.07,-.38],[.24,.24,-.32],'metal_edge','shoulder_plate')
 for x in (-.20,-.08,.04,.16):box(RIGHT,[x,.07,-.40],[x+.07,.18,-.37],'reactor')
 box(HEAD,[.13,.01,-.817],[.46,.21,-.73],'mechanism','optic_socket')
 box(HEAD,[.20,.06,-.835],[.40,.16,-.815],'metal_edge','optic',front='optic')
 for i,e in enumerate(DATA['mechanical_hand']):
  result.append({'node':HAND,'from':e['from'],'to':e['to'],'faces':{s:f['texture'][1:] for s,f in e['faces'].items()},'part':'arm_r','mechanical':True,'role':e.get('role'),'source_name':'approved_hand_'+str(i),'approved_hand':i})
 for i,e in enumerate(DATA['horns']):
  result.append({'node':HEAD,'from':e['from'],'to':e['to'],'faces':{s:'horn' for s in e['faces']},'part':'head','mechanical':False,'role':'antler','source_name':'retained_antler_'+str(i),'local_rotation':e['rotation']})
 return result
EXTRAS=extras()

@functools.lru_cache(maxsize=256)
def _model(frame=None,attack=None,kind='slam'):
 clip=('idle' if kind=='idle' else 'walk') if frame is not None else 'smash' if attack is not None and kind=='slam' else 'attack1' if attack is not None and kind=='swipe' else 'attack2' if attack is not None and kind=='throw' else 'idle'
 duration=DATA['clips'][clip]['duration']
 if frame is not None:time=duration*(frame%24)/24
 elif attack is not None and clip!='idle':
  # Rise through the strike, then settle back to the same rest pose. The first
  # and last throw frames match so a repeated barrage has no hard seam.
  phase=max(0,min(7,attack))/7
  time=duration*.72*math.sin(math.pi*phase)**2
 else:time=0
 worlds=transforms(clip,time,kind,attack);elements=[]
 for source_index,c in enumerate(DATA['cubes']+EXTRAS):
  if c.get('hand'):continue
  R,T=worlds[c['node']];uniform=math.sqrt(sum(R[k][0]**2 for k in range(3)));R=[[R[i][j]/uniform for j in range(3)] for i in range(3)]
  origin=T
  if c.get('local_rotation'):
   local=c['local_rotation'];pivot=local['origin'];L=rotation(local['axis'],local['angle']);origin=add(vec(R,[uniform*v for v in pivot]),T)
   # Bounds are relative to the new local pivot, rotated only through R*L.
   a=[uniform*(c['from'][k]-pivot[k]) for k in range(3)];b=[uniform*(c['to'][k]-pivot[k]) for k in range(3)];R=mul(R,L)
  else:a=[uniform*v for v in c['from']];b=[uniform*v for v in c['to']]
  aa=point(add(a,origin));bb=point(add(b,origin));rotation_angles=angles(R)
  faces={}
  for side,texture in c['faces'].items():
   if c.get('mechanical') and texture.startswith('father_glb_'):
    # Shape is retained; only the right half's material is replaced.
    texture='steel' if c['part'] in ('head','torso') else 'metal_edge' if side in ('up','down') else 'steel'
   faces[side]={'uv':[0,0,16,16],'texture':'#'+texture}
  e={'source_index':source_index,'from':aa,'to':bb,'faces':faces,'source_node':c['node'],'source_name':c['source_name'],'name':c['part'],'role':c.get('role','source_cube')}
  if max(abs(v) for v in rotation_angles)>1e-7:e['rotation']={'origin':point(origin),**dict(zip('xyz',[round(v,8) for v in rotation_angles])),'rescale':False}
  if c.get('light_emission'):e['light_emission']=c['light_emission']
  if 'approved_hand' in c:e['approved_hand']=c['approved_hand']
  elements.append(e)
 used=sorted({f['texture'][1:] for e in elements for f in e['faces'].values()})
 return {'elements':elements,'textures':{n:'yetiboss:boss/'+(n if n.startswith('father_glb_') else 'father_'+n) for n in used},'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}},'source_asset_sha256':DATA['source_sha256'],'source_animation':clip,'source_time':time}
def model(frame=None,attack=None,kind='slam'):return copy.deepcopy(_model(frame,attack,kind))
