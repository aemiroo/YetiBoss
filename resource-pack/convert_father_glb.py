"""One-time conversion of the user-supplied animated GLB; builds need no third-party libraries."""
import sys,json,io,base64,hashlib,pathlib
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
from import_gltf import load
from png_codec import encode
p=pathlib.Path(sys.argv[1]);j,bufs,acc=load(p);out=pathlib.Path(__file__).parent/'imported/father';out.mkdir(parents=True,exist_ok=True)
im=j['images'][0];v=j['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);tex=np.asarray(Image.open(io.BytesIO(bufs[v['buffer']][start:start+v['byteLength']])).convert('RGBA'))
worlds={};paths={}
def walk(i,parent,path):
 n=j['nodes'][i];M=np.eye(4);M[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));M[:3,3]=n.get('translation',[0,0,0]);worlds[i]=parent@M;paths[i]=path+[i]
 for c in n.get('children',[]):walk(c,worlds[i],paths[i])
for i in j['scenes'][0]['nodes']:walk(i,np.eye(4),[])
textures={};dedup={};cubes=[]
for i,n in enumerate(j['nodes']):
 if 'mesh' not in n:continue
 pr=j['meshes'][n['mesh']]['primitives'][0];P=acc(pr['attributes']['POSITION']);N=acc(pr['attributes']['NORMAL']);UV=acc(pr['attributes']['TEXCOORD_0']);a=P.min(0);b=P.max(0)
 assert all(len(np.unique(np.round(P[:,k],5)))<=2 for k in range(3)),(i,'non-cuboid')
 assert np.all(b>a),(i,'degenerate cuboid')
 names=[j['nodes'][k]['name'] for k in paths[i]];part='head' if 115 in paths[i] else 'arm_r' if 153 in paths[i] else 'arm_l' if 134 in paths[i] else 'leg_r' if 49 in paths[i] else 'leg_l' if 24 in paths[i] else 'torso'
 # Body and skull boxes crossing the anatomical midline get true UV-cropped halves.
 ranges=[(a.copy(),b.copy())];M=worlds[i];left=a[0]*M[0,0]+M[0,3];right=b[0]*M[0,0]+M[0,3]
 if part in ('torso','head') and abs(M[0,1])+abs(M[0,2])<1e-5 and left<-1e-5<right and right>1e-5:
  cut=-M[0,3]/M[0,0];aa=a.copy();bb=b.copy();bb[0]=cut;aa[0]=cut;ranges=[(a.copy(),bb),(aa,b.copy())]
 for aa,bb in ranges:
  center=worlds[i][:3,:3]@((aa+bb)/2)+worlds[i][:3,3];mechanical=part in ('arm_r','leg_r') or (part in ('torso','head') and center[0]>1e-5)
  faces={}
  for norm in np.unique(N.round(5),axis=0):
   ids=np.where(np.max(abs(N-norm),axis=1)<1e-4)[0];pts=P[ids];uv=UV[ids];axis=int(np.argmax(abs(norm)));side={0:('west','east'),1:('down','up'),2:('north','south')}[axis][int(norm[axis]>0)]
   def st(pts):
    if side=='north':return np.stack(((b[0]-pts[:,0])/(b[0]-a[0]),(b[1]-pts[:,1])/(b[1]-a[1])),1)
    if side=='south':return np.stack(((pts[:,0]-a[0])/(b[0]-a[0]),(b[1]-pts[:,1])/(b[1]-a[1])),1)
    if side=='west':return np.stack(((pts[:,2]-a[2])/(b[2]-a[2]),(b[1]-pts[:,1])/(b[1]-a[1])),1)
    if side=='east':return np.stack(((b[2]-pts[:,2])/(b[2]-a[2]),(b[1]-pts[:,1])/(b[1]-a[1])),1)
    if side=='up':return np.stack(((pts[:,0]-a[0])/(b[0]-a[0]),(pts[:,2]-a[2])/(b[2]-a[2])),1)
    return np.stack(((pts[:,0]-a[0])/(b[0]-a[0]),(b[2]-pts[:,2])/(b[2]-a[2])),1)
   A=np.column_stack((st(pts),np.ones(len(pts))));coef=np.linalg.lstsq(A,uv,rcond=None)[0];assert np.max(abs(A@coef-uv))<1e-5
   # Sample the actual retained section rather than stretching the full face into each half.
   Y,X=np.mgrid[0:16,0:16];u=(X.ravel()+.5)/16;vv=(Y.ravel()+.5)/16;sample=np.empty((256,3))
   if side=='north':sample[:,0]=bb[0]-u*(bb[0]-aa[0]);sample[:,1]=bb[1]-vv*(bb[1]-aa[1]);sample[:,2]=aa[2]
   elif side=='south':sample[:,0]=aa[0]+u*(bb[0]-aa[0]);sample[:,1]=bb[1]-vv*(bb[1]-aa[1]);sample[:,2]=bb[2]
   elif side=='west':sample[:,0]=aa[0];sample[:,1]=bb[1]-vv*(bb[1]-aa[1]);sample[:,2]=aa[2]+u*(bb[2]-aa[2])
   elif side=='east':sample[:,0]=bb[0];sample[:,1]=bb[1]-vv*(bb[1]-aa[1]);sample[:,2]=bb[2]-u*(bb[2]-aa[2])
   elif side=='up':sample[:,0]=aa[0]+u*(bb[0]-aa[0]);sample[:,1]=bb[1];sample[:,2]=aa[2]+vv*(bb[2]-aa[2])
   else:sample[:,0]=aa[0]+u*(bb[0]-aa[0]);sample[:,1]=aa[1];sample[:,2]=bb[2]-vv*(bb[2]-aa[2])
   coords=np.column_stack((st(sample),np.ones(256)))@coef;tx=np.clip((coords[:,0]*tex.shape[1]).astype(int),0,tex.shape[1]-1);ty=np.clip((coords[:,1]*tex.shape[0]).astype(int),0,tex.shape[0]-1);patch=tex[ty,tx].reshape((16,16,4));key=patch.tobytes()
   if key not in dedup:
    label='father_glb_'+str(len(dedup));dedup[key]=label;textures[label]=base64.b64encode(encode(16,16,patch.tobytes())).decode()
   faces[side]=dedup[key]
  if len(ranges)>1:faces.pop('east' if bb[0]<=-M[0,3]/M[0,0]+1e-8 else 'west',None)
  cubes.append({'node':i,'from':aa.tolist(),'to':bb.tolist(),'faces':faces,'part':part,'mechanical':bool(mechanical),'source_name':n['name'],'hand':151 in paths[i]})
clips={}
for an in j['animations']:
 channels=[];duration=0
 for c in an['channels']:
  s=an['samplers'][c['sampler']];times=acc(s['input']).ravel();values=acc(s['output']);duration=max(duration,float(times.max()))
  assert s.get('interpolation','LINEAR') in ('LINEAR','STEP')
  channels.append({'node':c['target']['node'],'path':c['target']['path'],'times':times.tolist(),'values':values.tolist(),'interpolation':s.get('interpolation','LINEAR')})
 clips[an['name']]={'duration':duration,'channels':channels}
# Preserve the previously approved mechanical hand, mounting it on the imported hand bone.
from boss_model import procedural_father_model as model
hand=[e for e in model()['elements'] if e.get('name')=='arm_r' and e.get('role') in ('fist','knuckle','thumb')]
# Undo only the previous resting translation before fitting the same shape to this rig.
for e in hand:
 for bound in ('from','to'):e[bound][2]+=1
lo=np.min([e['from'] for e in hand],0);hi=np.max([e['to'] for e in hand],0);target_lo=np.array([-.2668,-.8671,-.4448]);target_hi=np.array([.2664,.2211,.2458]);factor=(target_hi-target_lo)/(hi-lo)
for e in hand:
 for bound in ('from','to'):e[bound]=(target_lo+(np.array(e[bound])-lo)*factor).tolist()
 e.pop('rotation',None)
horns=[e for e in model()['elements'] if e.get('role')=='antler']
for e in horns:
 for bound in ('from','to'):
  x,y,z=e[bound];e[bound]=[(x-8)*.22,(y-9.11)*.22+.26,(z-4.4)*.22-.4]
 if 'rotation' in e:
  x,y,z=e['rotation']['origin'];e['rotation']['origin']=[(x-8)*.22,(y-9.11)*.22+.26,(z-4.4)*.22-.4]
data={'horns':horns,'source_name':p.name,'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_meshes':len(j['meshes']),'nodes':j['nodes'],'roots':j['scenes'][0]['nodes'],'cubes':cubes,'clips':clips,'mechanical_hand':hand}
(out/'scene.json').write_text(json.dumps(data,separators=(',',':')));(out/'textures.json').write_text(json.dumps(textures,separators=(',',':')))
(out/'SOURCES.md').write_text('User-supplied animated Yeti GLB\n\nSource: '+p.name+'\nSHA-256: '+data['source_sha256']+'\n\nThe converted mesh, UV patches and all six source animation clips are retained. Original asset rights remain with their creator; author and license information were not included in the supplied GLB. This third-party asset is not covered by the repository code license.\n')
print('Converted',len(cubes),'cuboids,',len(textures),'face textures,',list(clips))
