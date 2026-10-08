"""Port our Java surface models to Bedrock attachables for GeyserDisplayEntity.

The extension and its own resource pack are installed separately; neither is
bundled here. All generated model/texture content remains original MIT content.
"""
import json, struct, zlib, zipfile
from build_pack import ROOT, MODELS, files as java_files

from gear_model import GEAR_MODELS,GEAR_ITEMS,icon as gear_icon
PETS = MODELS+GEAR_MODELS

def encoded(value):
    return json.dumps(value, indent=2).encode()

def pixels(data):
    # Preserve all 16x16 RGBA texels from our filter-zero PNG textures.
    pos = 8
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        if data[pos+4:pos+8] == b'IDAT':
            return b''.join(zlib.decompress(data[pos+8:pos+8+length])[i*65+1:i*65+65] for i in range(16))
        pos += 12 + length
    raise ValueError('Missing PNG pixels')

def atlas(colors):
    def chunk(kind, data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    width = 16 * len(colors)
    raw = b''.join(b'\0'+b''.join(c[y*64:(y+1)*64] for c in colors) for y in range(16))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,16,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def tga(colors):
    # Solid emissive materials interpret alpha as a light mask; zero is full glow.
    width=16*len(colors)
    header=struct.pack('<BBBHHBHHHHBB',0,0,2,0,0,0,0,0,width,16,32,0x28)
    row=b''.join(bytes((c[2],c[1],c[0],c[3]))*16 for c in colors)
    return header+row*16

def geometry(pet, model, names):
    cubes = []
    glowing = []
    translate = model['display']['fixed']['translation']
    gear=pet in GEAR_MODELS
    for element in model['elements']:
        a, b = element['from'], element['to']
        uv = {}
        for face, definition in element['faces'].items():
            # Mirroring Java's X axis swaps east and west; north stays -Z.
            bedrock_face = {'east':'west','west':'east'}.get(face,face)
            tile = names.index(definition['texture'][1:])
            uv[bedrock_face] = {'uv':[tile*16,0], 'uv_size':[16,16]}
        destination = glowing if element.get('light_emission',0) else cubes
        cube={'origin':[8-b[0]-translate[0],a[1]+translate[1]-(8 if gear else 0),a[2]-8+translate[2]],
                      'size':[b[i]-a[i] for i in range(3)],'uv':uv}
        if 'rotation' in element:
            rotation=element['rotation']
            px,py,pz=rotation['origin']
            cube['pivot']=[8-px-translate[0],py+translate[1],pz-8+translate[2]]
            # Bedrock cube rotations use the opposite X rotation convention.
            cube['rotation']=[-rotation['angle'] if rotation['axis']=='x' else 0,
                              rotation['angle'] if rotation['axis']=='y' else 0,
                              rotation['angle'] if rotation['axis']=='z' else 0]
        destination.append(cube)
    # The extension's geyser_z bone is at Y=8, with mapping y-offset=-0.5.
    # This keeps Java's item centre (and pumpkin's fixed translation) aligned.
    bones=[{'name':'pet','binding':('query.item_slot_to_bone_name(context.item_slot)' if gear else "'geyser_z'"),'pivot':([0,0,0] if gear else [0,8,0]),'cubes':cubes}]
    if glowing:
        bones.append({'name':'pet_light','parent':'pet','pivot':[0,8,0],'cubes':glowing})
    return {'format_version':'1.16.0','minecraft:geometry':[{
        'description':{'identifier':'geometry.yetiboss.'+pet,
                       'texture_width':16*len(names),'texture_height':16,
                       'visible_bounds_width':3,'visible_bounds_height':3,
                       'visible_bounds_offset':[0,0.5,0]},
        'bones':bones}]}

def files():
    source = java_files()
    result = {'manifest.json':encoded({'format_version':2,
        'header':{'name':'YetiBoss Bedrock','description':'Original Father and Mother Yeti bosses',
                  'uuid':'f5d7fcef-34a7-48fa-a98f-2155802ef6e4','version':[0,6,3],'min_engine_version':[1,21,0]},
        'modules':[{'type':'resources','uuid':'ec728d89-387d-4a04-bdb0-7263d53d0a33','version':[0,6,3]}]}),
        'LICENSE.txt':source['LICENSE.txt'],
        'render_controllers/yetiboss.json':encoded({'format_version':'1.8.0','render_controllers':{
            'controller.render.yetiboss':{'geometry':'Geometry.default',
                'materials':[{'*':'Material.default'}],'textures':['Texture.default']}}})}
    controllers=json.loads(result['render_controllers/yetiboss.json'])
    controllers['render_controllers']['controller.render.yetiboss.pumpkin']={
        'geometry':'Geometry.default','materials':[{'*':'Material.default'},{'pet_light':'Material.glow'}],
        'textures':['Texture.default']}
    result['render_controllers/yetiboss.json']=encoded(controllers)
    from build_pack import SOUNDS
    result['sounds/sound_definitions.json']=encoded({'format_version':'1.14.0','sound_definitions':{
        'yetiboss.'+name:{'category':'hostile','sounds':['sounds/yetiboss/'+name]} for name in SOUNDS}})
    for name in SOUNDS:
        result['sounds/yetiboss/'+name+'.ogg']=source['assets/yetiboss/sounds/'+name+'.ogg']
    texture_data = {}
    for pet in PETS:
        model = json.loads(source['assets/yetiboss/models/'+('gear' if pet in GEAR_MODELS else 'boss')+'/'+pet+'.json'])
        names = list(model['textures'])
        colors = [pixels(source['assets/'+model['textures'][n].replace(':','/textures/')+'.png']) for n in names]
        if pet=='pumpkin':
            mask=[c[:3]+bytes([0 if n=='pumpkin_glow' else 255])
                  for n,c in zip(names,colors)]
            result['textures/yetiboss/'+pet+'.tga'] = tga(mask)
            result['textures/yetiboss/'+pet+'_icon.png'] = atlas(colors)
        else:
            result['textures/yetiboss/'+pet+'.png'] = atlas(colors)
        if pet in GEAR_MODELS:result['textures/yetiboss/'+pet+'_icon.png']=gear_icon(pet)
        result['models/entity/'+pet+'.geo.json'] = encoded(geometry(pet,model,names))
        result['attachables/'+pet+'.json'] = encoded({'format_version':'1.10.0','minecraft:attachable':{
            'description':{'identifier':'yetiboss:'+pet,
                'materials':({'default':'entity_alphablend'} if pet=='ghost' else
                             ({'default':'entity_alphatest','glow':'entity_emissive'} if pet=='pumpkin' else {'default':'entity_alphatest'})),
                'textures':{'default':'textures/yetiboss/'+pet},
                'geometry':{'default':'geometry.yetiboss.'+pet},
                'render_controllers':['controller.render.yetiboss'+('.pumpkin' if pet=='pumpkin' else '')]}}})
        texture_data['yetiboss.'+pet] = {'textures':'textures/yetiboss/'+pet+('_icon' if pet=='pumpkin' or pet in GEAR_MODELS else '')}
    result['textures/item_texture.json'] = encoded({'resource_pack_name':'YetiBoss','texture_name':'atlas.items','texture_data':texture_data})
    return result

def mappings():
    items={'minecraft:paper':[
        {'type':'definition','model':'yetiboss:'+pet,'bedrock_identifier':'yetiboss:'+pet,
         'display_name':pet.title()+' Boss'} for pet in MODELS]}
    for name,base in GEAR_ITEMS.items():
        items[base]=[{'type':'definition','model':'yetiboss:'+name,'bedrock_identifier':'yetiboss:'+name,
                      'display_name':{'frostfang':'Frostfang','frostbow':'Frost Bow','frostpickaxe':'Glacier Pickaxe'}[name]}]
    return {'format_version':2,'items':items}

def display_mappings():
    return 'mappings:\n'+''.join('  yetiboss_'+pet+':\n    type: "minecraft:paper"\n    item-identifier: "yetiboss:'+pet+'"\n    displayentityoptions:\n      y-offset: -0.5\n      vanilla-scale: false\n      vanilla-scale-multiplier: 1\n      hand: false\n' for pet in MODELS)

if __name__ == '__main__':
    target = ROOT/'target'
    target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target/'YetiBoss-Bedrock.mcpack','w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(files().items()):
            info=zipfile.ZipInfo(name,(2026,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,data)
    (target/'yetiboss-geyser-mappings.json').write_bytes(encoded(mappings()))
    (target/'yetiboss-display-mappings.yml').write_text(display_mappings())
    print('Built Bedrock pack and both Geyser mapping files')
