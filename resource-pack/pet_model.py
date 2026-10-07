"""CosmeticPets model helpers, MIT licensed; pinned source recorded below."""
import math

def limb(pet, cell):
    x,y,z=cell
    if pet=='reindeer' and y<5 and x in (5,10) and z in (7,11):
        return ('leg',x,z)
    if pet=='yeti':
        if y<3 and x in (5,6,9,10) and 5<=z<10:
            return ('leg',0 if x<8 else 1)
        if (1<=x<4 or 12<=x<15) and 1<=y<10 and 6<=z<11:
            return ('arm',0 if x<8 else 1)
    return None

def winter_model(pet, articulated=False):
    # Unite solid voxels first: only external faces are emitted, avoiding seams.
    cells={}
    def box(a,b,material):
        for x in range(a[0],b[0]):
            for y in range(a[1],b[1]):
                for z in range(a[2],b[2]): cells[x,y,z]=material
    def ball(center,radii,material):
        for x in range(16):
            for y in range(16):
                for z in range(16):
                    if sum(((v+.5-c)/d)**2 for v,c,d in zip((x,y,z),center,radii))<=1:
                        cells[x,y,z]=material
    if pet=='yeti':
        # Original baby silhouette inspired by the supplied long-armed reference.
        box((4,2,5),(12,10,12),'yeti_cream')
        box((4,9,4),(12,14,11),'yeti_cream')
        box((1,1,6),(4,10,11),'yeti_cream')
        box((12,1,6),(15,10,11),'yeti_cream')
        box((5,0,5),(7,3,10),'yeti_cream')
        box((9,0,5),(11,3,10),'yeti_cream')
        # Small horns wrap down the sides, rather than projecting above the head.
        # Thick side roots taper forward and down into a curved three-dimensional tip.
        box((2,12,4),(5,14,8),'yeti_horn')
        box((2,11,3),(4,13,5),'yeti_horn')
        box((3,10,2),(4,12,4),'yeti_horn')
        box((11,12,4),(14,14,8),'yeti_horn')
        box((12,11,3),(14,13,5),'yeti_horn')
        box((12,10,2),(13,12,4),'yeti_horn')
        # Flat face: all facial colours occupy the same surface plane.
        box((5,9,4),(11,12,5),'yeti_face')
        box((5,11,4),(7,12,5),'yeti_blue')
        box((9,11,4),(11,12,5),'yeti_blue')
        box((6,11,4),(7,12,5),'coal')
        box((9,11,4),(10,12,5),'coal')
        box((7,10,4),(9,11,5),'yeti_nose')
        box((6,9,4),(10,10,5),'yeti_smile')
        # A repeatable voxel fur pattern is preserved in both pack formats.
        for (x,y,z),material in list(cells.items()):
            if material=='yeti_cream':
                stripe=(x*7+z*11+(y//2)*3)%17
                cells[x,y,z]='yeti_fur_shadow' if stripe<3 else ('yeti_fur_light' if stripe==5 else material)
    elif pet=='snowman':
        ball((8,4,8),(4,4,4),'snow')
        ball((8,8,8),(3,3,3),'snow')
        ball((8,11,8),(2.5,2.5,2.5),'snow')
        box((6,13,6),(10,14,10),'coal')
        box((7,14,7),(9,16,9),'coal')
        box((5,8,5),(11,9,11),'scarf')
        box((5,6,4),(7,9,5),'scarf')
        box((6,11,5),(7,12,6),'coal'); box((9,11,5),(10,12,6),'coal')
        box((7,10,3),(9,11,6),'carrot')
        box((7,4,4),(8,5,5),'coal'); box((7,6,5),(8,7,6),'coal')
        box((3,6,7),(5,7,8),'wood'); box((11,6,7),(13,7,8),'wood')
        box((3,4,7),(4,6,8),'wood'); box((12,4,7),(13,6,8),'wood')
    else:
        ball((8,6,9),(4,3,4),'fur')
        box((6,6,4),(10,10,7),'fur')
        ball((8,10,5),(3,2.5,3),'fur')
        box((6,9,1),(10,11,4),'muzzle')
        box((7,10,0),(9,11,1),'red_nose')
        box((5,11,2),(6,12,3),'coal'); box((10,11,2),(11,12,3),'coal')
        box((3,11,5),(5,13,7),'fur'); box((11,11,5),(13,13,7),'fur')
        for x in (5,10):
            for z in (7,11):
                box((x,1,z),(x+1,5,z+1),'fur'); box((x,0,z),(x+1,1,z+1),'coal')
        box((7,6,13),(9,8,15),'muzzle')
        box((5,7,4),(11,8,7),'scarf')
        for x in (5,10):
            box((x,12,5),(x+1,16,6),'antler')
        box((3,14,5),(6,15,6),'antler'); box((10,14,5),(13,15,6),'antler')
        box((3,15,5),(4,16,6),'antler'); box((12,15,5),(13,16,6),'antler')
    directions={'west':(-1,0,0),'east':(1,0,0),'down':(0,-1,0),
                'up':(0,1,0),'north':(0,0,-1),'south':(0,0,1)}
    elements=[]
    for (x,y,z),material in sorted(cells.items()):
        faces={f:{'uv':[0,0,16,16],'texture':'#'+material}
               for f,(dx,dy,dz) in directions.items()
               if (x+dx,y+dy,z+dz) not in cells or
               (articulated and limb(pet,(x,y,z))!=limb(pet,(x+dx,y+dy,z+dz)))}
        if faces: elements.append({'from':[x,y,z],'to':[x+1,y+1,z+1],'faces':faces})
    names=sorted({e['texture'][1:] for c in elements for e in c['faces'].values()})
    return {'credit':'Original CosmeticPets Christmas companion.',
            'textures':{n:'cosmeticpets:pet/'+n for n in names},'elements':elements,
            'display':{'fixed':{'rotation':[0,0,0],'translation':[0,8,0],'scale':[1,1,1]}}}

def walk_model(pet, frame):
    # Closed surfaces at each joint prevent holes when limbs rotate away.
    model=winter_model(pet, articulated=True)
    swing=math.sin(2*math.pi*frame/12)
    for element in model['elements']:
        part=limb(pet, element['from'])
        if part is None: continue
        if pet=='reindeer':
            _,x,z=part
            # Vanilla quadruped gait: diagonal legs swing together.
            sign=1 if (x,z) in ((5,7),(10,11)) else -1
            pivot=[x+.5,5,z+.5]
            angle=28*swing*sign
        else:
            kind,side=part
            sign=1 if side==0 else -1
            if kind=='arm':
                pivot=[2.5 if side==0 else 13.5,9,8.5]
                # Iron golem arms swing together, using a triangular cycle.
                golem_swing=1-4*abs((frame/12+.25)%1-.5)
                angle=-18*golem_swing
            else:
                pivot=[6 if side==0 else 10,3,7.5]
                angle=25*swing*sign
        element['rotation']={'origin':pivot,'axis':'x',
                             'angle':round(angle,6),'rescale':False}
    return model

def yeti_walk_model(frame):
    return walk_model('yeti',frame)

# Source: https://github.com/aemiroo/CosmeticPets/blob/06dc12a18443f0601180b508a26c052cb7193309/resource-pack/build_pack.py
