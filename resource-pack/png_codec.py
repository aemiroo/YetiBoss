"""Small standard-library RGBA PNG codec for resource-pack build tooling."""
import struct,zlib

def decode(data):
 p=8;compressed=b''
 while p<len(data):
  n=struct.unpack_from('>I',data,p)[0];kind=data[p+4:p+8];payload=data[p+8:p+8+n];p+=n+12
  if kind==b'IHDR':w,h,depth,color,*_=struct.unpack('>IIBBBBB',payload);assert depth==8 and color==6
  elif kind==b'IDAT':compressed+=payload
 raw=zlib.decompress(compressed);stride=w*4;prev=bytearray(stride);rows=[]
 for y in range(h):
  f=raw[y*(stride+1)];row=bytearray(raw[y*(stride+1)+1:(y+1)*(stride+1)])
  for x in range(stride):
   a=row[x-4] if x>=4 else 0;b=prev[x];c=prev[x-4] if x>=4 else 0
   if f==1:v=a
   elif f==2:v=b
   elif f==3:v=(a+b)//2
   elif f==4:
    v=a+b-c;pa,pb,pc=abs(v-a),abs(v-b),abs(v-c);v=a if pa<=pb and pa<=pc else b if pb<=pc else c
   else:v=0
   row[x]=(row[x]+v)&255
  rows.append(bytes(row));prev=row
 return w,h,b''.join(rows)

def encode(w,h,rgba):
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 raw=b''.join(b'\0'+rgba[y*w*4:(y+1)*w*4] for y in range(h))
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
