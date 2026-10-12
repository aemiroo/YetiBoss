"""Exact cuboid rasterizer shared by preview and Bedrock item icon builds."""
import math
from png_codec import decode
FACES={'north':[3,2,0,1],'south':[6,7,5,4],'west':[2,6,4,0],'east':[7,3,1,5],'up':[2,3,7,6],'down':[4,5,1,0]}
NORMALS={'north':(0,0,-1),'south':(0,0,1),'west':(-1,0,0),'east':(1,0,0),'up':(0,1,0),'down':(0,-1,0)}
def rotate(v,r):
 x,y,z=v
 for axis in 'xyz':
  angle=r.get('angle',0) if r.get('axis')==axis else r.get(axis,0);c=math.cos(math.radians(angle));s=math.sin(math.radians(angle))
  if axis=='x':y,z=y*c-z*s,y*s+z*c
  elif axis=='y':x,z=x*c+z*s,-x*s+z*c
  else:x,y=x*c-y*s,x*s+y*c
 return x,y,z

def raster(model,textures,w,h,scale,yaw=.28,center=(8,8,8)):
 tex={n:decode(d) for n,d in textures.items()};pixels=bytearray(w*h*4);depth=[-float('inf')]*(w*h);c,s=math.cos(yaw),math.sin(yaw)
 def project(v):
  x,y,z=(q-t for q,t in zip(v,center));return (w/2+(x*c+z*s)*scale,h/2-y*scale,(x*s-z*c))
 for e in model['elements']:
  a,b=e['from'],e['to'];vs=[(x,y,z) for z in (a[2],b[2]) for y in (a[1],b[1]) for x in (a[0],b[0])];r=e.get('rotation',{});o=r.get('origin',[0,0,0])
  if r:vs=[tuple(t+q for t,q in zip(rotate(tuple(q-t for q,t in zip(v,o)),r),o)) for v in vs]
  for face,d in e['faces'].items():
   normal=rotate(NORMALS[face],r)
   if normal[0]*s-normal[2]*c<=1e-8:continue
   shade=.72+.28*max(0,-normal[0]*.4+normal[1]*.7-normal[2]*.6)
   p=[project(vs[i]) for i in FACES[face]];uv=[(0,0),(1,0),(1,1),(0,1)];tw,th,data=tex[d['texture'][1:]]
   for ids in ((0,1,2),(0,2,3)):
    t=[p[i] for i in ids];u=[uv[i] for i in ids];den=(t[1][1]-t[2][1])*(t[0][0]-t[2][0])+(t[2][0]-t[1][0])*(t[0][1]-t[2][1])
    if abs(den)<1e-8:continue
    for y in range(max(0,int(min(v[1] for v in t))),min(h,int(max(v[1] for v in t))+2)):
     for x in range(max(0,int(min(v[0] for v in t))),min(w,int(max(v[0] for v in t))+2)):
      A=((t[1][1]-t[2][1])*(x+.5-t[2][0])+(t[2][0]-t[1][0])*(y+.5-t[2][1]))/den;B=((t[2][1]-t[0][1])*(x+.5-t[2][0])+(t[0][0]-t[2][0])*(y+.5-t[2][1]))/den;C=1-A-B
      if min(A,B,C)<-1e-7:continue
      z=A*t[0][2]+B*t[1][2]+C*t[2][2];idx=y*w+x
      if z<=depth[idx]:continue
      U=A*u[0][0]+B*u[1][0]+C*u[2][0];V=A*u[0][1]+B*u[1][1]+C*u[2][1];tx=max(0,min(tw-1,int(U*tw)));ty=max(0,min(th-1,int(V*th)));k=(ty*tw+tx)*4
      if data[k+3]<13:continue
      pixels[idx*4:idx*4+4]=bytes([min(255,int(data[k+i]*shade)) for i in range(3)]+[data[k+3]]);depth[idx]=z
 return bytes(pixels)
