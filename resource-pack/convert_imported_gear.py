import sys,json,pathlib,base64,io,math
import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from import_gltf import load
root=pathlib.Path(__file__).parent/'imported';root.mkdir(exist_ok=True);registry={};material={}
source_root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('/tmp/inspect_frost')
for name,folder,basis in [('frostfang','ice-sword',np.eye(3)),('frostpickaxe','ice-pickaxe-free-download',Rotation.from_euler('y',-90,degrees=True).as_matrix()),('frostbow','hytale-frost-bow',Rotation.from_euler('z',90,degrees=True).as_matrix())]:
 p=next((source_root/folder/'source').iterdir());j,bufs,acc=load(p)
 images=[]
 for im in j['images']:
  if 'uri' in im:
   uri=im['uri'];data=base64.b64decode(uri.split(',')[1]) if uri.startswith('data:') else (p.parent/uri).read_bytes()
  else:
   v=j['bufferViews'][im['bufferView']];data=bufs[v['buffer']][v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
  images.append(np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')))
 worlds={}
 def walk(i,parent):
  n=j['nodes'][i];M=np.eye(4);M[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));M[:3,3]=n.get('translation',[0,0,0]);worlds[i]=parent@M
  for c in n.get('children',[]):walk(c,worlds[i])
 for i in j['scenes'][j.get('scene',0)]['nodes']:walk(i,np.eye(4))
 if name=='frostbow':basis=Rotation.from_euler('z',90,degrees=True).as_matrix()@worlds[0][:3,:3].T
 objects=[];allverts=[]
 for i,n in enumerate(j['nodes']):
  if 'mesh' not in n:continue
  M=worlds[i];R=basis@M[:3,:3];T=basis@M[:3,3];prims=j['meshes'][n['mesh']]['primitives'];verts=np.concatenate([acc(pr['attributes']['POSITION']) for pr in prims]);a=verts.min(0);b=verts.max(0)
  assert all(len(np.unique(np.round(verts[:,k],5)))<=2 for k in range(3)),(name,i,'not cuboid')
  allverts.append(verts@R.T+T);objects.append((i,n,R,T,a,b,prims))
 allverts=np.concatenate(allverts);lo=allverts.min(0);hi=allverts.max(0);scale=14.7/max(hi-lo);offset=8-(lo+hi)/2*scale
 es=[];unique={}
 for i,n,R,T,a,b,prims in objects:
  # Cuboid retains local axes, with world rotation applied about its original origin.
  elem={'from':(a*scale+T*scale+offset).tolist(),'to':(b*scale+T*scale+offset).tolist(),'faces':{}}
  angles=Rotation.from_matrix(R).as_euler('xyz',degrees=True)
  assert np.max(abs(Rotation.from_euler('xyz',angles,degrees=True).as_matrix()-R))<1e-6, 'Rotation changed during export'
  if max(abs(angles))>1e-7:elem['rotation']={'origin':(T*scale+offset).tolist(),'x':float(angles[0]),'y':float(angles[1]),'z':float(angles[2])}
  for pr in prims:
   P=acc(pr['attributes']['POSITION']);N=acc(pr['attributes']['NORMAL']);UV=acc(pr['attributes']['TEXCOORD_0']);mi=pr.get('material',0);ti=j['materials'][mi]['pbrMetallicRoughness']['baseColorTexture']['index'];tex=images[j['textures'][ti]['source']]
   for norm in np.unique(N.round(5),axis=0):
    ids=np.intersect1d(np.where(np.max(abs(N-norm),axis=1)<1e-4)[0],np.unique(acc(pr['indices']).ravel()));
    if len(ids)<3:continue
    pts=P[ids];uv=UV[ids];axis=int(np.argmax(abs(norm)));side={0:('west','east'),1:('down','up'),2:('north','south')}[axis][int(norm[axis]>0)]
    # Java default face coordinates, from upper-left toward lower-right.
    if side=='north':s=b[0]-pts[:,0];t=b[1]-pts[:,1];ws=b[0]-a[0];ht=b[1]-a[1]
    elif side=='south':s=pts[:,0]-a[0];t=b[1]-pts[:,1];ws=b[0]-a[0];ht=b[1]-a[1]
    elif side=='west':s=pts[:,2]-a[2];t=b[1]-pts[:,1];ws=b[2]-a[2];ht=b[1]-a[1]
    elif side=='east':s=b[2]-pts[:,2];t=b[1]-pts[:,1];ws=b[2]-a[2];ht=b[1]-a[1]
    elif side=='up':s=pts[:,0]-a[0];t=pts[:,2]-a[2];ws=b[0]-a[0];ht=b[2]-a[2]
    else:s=pts[:,0]-a[0];t=b[2]-pts[:,2];ws=b[0]-a[0];ht=b[2]-a[2]
    if ws<1e-8 or ht<1e-8:continue
    A=np.stack((s/ws,t/ht,np.ones(len(ids))),axis=1);coef=np.linalg.lstsq(A,uv,rcond=None)[0]
    assert np.max(abs(A@coef-uv))<1e-5
    Y,X=np.mgrid[0:64,0:64];sample=np.stack(((X+.5)/64,(Y+.5)/64,np.ones((64,64))),axis=-1)@coef
    tx=np.clip((sample[:,:,0]*tex.shape[1]).astype(int),0,tex.shape[1]-1);ty=np.clip((sample[:,:,1]*tex.shape[0]).astype(int),0,tex.shape[0]-1);patch=tex[ty,tx];key=patch.tobytes()
    if key not in unique:
     label=name+'_face_'+str(len(unique));unique[key]=label;f=io.BytesIO();Image.fromarray(patch).save(f,format='PNG');material[label]=base64.b64encode(f.getvalue()).decode()
    label=unique[key];elem['faces'][side]={'uv':[0,0,16,16],'texture':'#'+label}
  es.append(elem)
 # Source grip is the centre of the first mesh's haft for tools; bow's root handle.
 if name!='frostbow':
  i,n,R,T,a,b,pr=objects[0];g=(a+b)/2;g[1]=a[1]+(b[1]-a[1])*.30;grip=(R@g+T)*scale+offset
 else:grip=(basis@worlds[0][:3,3])*scale+offset
 data={'textures':{v:'yetiboss:gear/'+v for v in unique.values()},'elements':es,'grip':grip.tolist(),'source_bounds':[lo.tolist(),hi.tolist()],'source_name':p.name,'nodes':[n['name'] for _,n,*_ in objects]}
 (root/(name+'.json')).write_text(json.dumps(data,separators=(',',':')))
 registry[name]=len(es);print(name,len(es),'textures',len(unique),'grip',grip)
(root/'textures.json').write_text(json.dumps(material,separators=(',',':')))
(root/'SOURCES.md').write_text('User-supplied third-party assets\n\n- Frostfang: ice-sword.zip / source/model.gltf\n- Glacier Pickaxe: ice-pickaxe-free-download.zip / source/model.gltf\n- Frost Bow: hytale-frost-bow.zip / source/Diamond Bow.glb\n\nOriginal geometry and textures retained. These assets are not covered by the repository code license. Author names and distribution licenses were not included in the uploaded archives.\n')
