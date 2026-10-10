import base64,json,struct,pathlib,numpy as np

def load(p):
 b=p.read_bytes()
 if p.suffix=='.glb':
  l=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+l]);off=20+l;bl=struct.unpack_from('<I',b,off)[0];bufs=[b[off+8:off+8+bl]]
 else:
  j=json.loads(b);bufs=[base64.b64decode(v['uri'].split(',')[1]) for v in j['buffers']]
 def acc(i):
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dtype={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',np.dtype(dtype).itemsize*n)
  return np.ndarray((a['count'],n),dtype=dtype,buffer=bufs[v['buffer']],offset=off,strides=(stride,np.dtype(dtype).itemsize)).copy()
 return j,bufs,acc
if __name__=='__main__':
 for p in pathlib.Path('/tmp/inspect_frost').glob('*/source/*'):
  j,bufs,acc=load(p);print(p)
  for i,m in enumerate(j['meshes']):
   xyz=np.concatenate([acc(pr['attributes']['POSITION']) for pr in m['primitives']]);print(i,len(xyz),[len(np.unique(np.round(xyz[:,k],6))) for k in range(3)],xyz.min(0).round(3),xyz.max(0).round(3))
