"""
MIT License

Copyright (c) 2020-2021 ossls

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


# This is a Blender python script. 
# When executed it will select all the objects in the scene
# and export them in a way that makes the compatible with Amazon Lumberyard.

import bpy
import os
import sys
from pathlib import Path

from bpy.app.handlers import persistent


def safe_relative_path(full_path, base_path):
    full_path = Path(full_path).resolve()
    base_path = Path(base_path).resolve()
    try:
        return str(full_path.relative_to(base_path))
    except ValueError:
        return str(full_path)  # Return as-is if not a subpath



basedir = os.path.dirname(bpy.data.filepath)
view_layer = bpy.context.view_layer

# When invoking this script, the destination folder needs
# to be passed in as a command line argument, you need to use
# Blender's -- command line option which does the following:
# -- "End option processing, following arguments passed unchanged. Access via Python's 'sys.argv'"
destinationPath = sys.argv[6]

# Once the .blend file is loaded, this function will select
# all the objects in Object mode, set Edit mode
# then export the scene as an FBX file that is compatible
# with Lumberyard. 
# 
# Currently it only exports the MESH.
#
def doExport(filePath):

    idx = sys.argv.index("--")
    custom_args = sys.argv[(idx + 1):] 
    content_root = custom_args[1]

    print("destinationPath: "  + destinationPath)
    print("filePath: "  + filePath)

    collection_name = ""

    generatedFBXFiles = []


    for collection in bpy.data.collections:
        collection_name = collection.name

        armature = None

        for obj in bpy.data.objects:

            # Skip non-mesh objects and hidden objects
            if obj.type != 'MESH' or obj.hide_get():
                continue

            # Find the armature that belongs to this object
            for armatureObj in bpy.data.objects:
                if armatureObj.type == 'ARMATURE':
                    print("FOUND ARMATURE: " + armatureObj.name)
                    if armatureObj.parent != None and armatureObj.parent == obj:
                        print("CHOSE ARMATURE: " + armatureObj.name + " parent: " + armatureObj.parent.name)
                        armature = armatureObj

            fbxName = f"{collection_name}_{obj.name}.fbx"
            fileName = f"{filePath}\\{fbxName}"

            # Select only the current object and its armature (if any)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Enter Edit Mode for cleanup
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
            bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.mesh.quads_convert_to_tris()
            bpy.ops.object.mode_set(mode='OBJECT')  # Back to Object Mode

            # Find and select the armature if it exists
            if armature != None:
                armature.select_set(True)
                bpy.context.view_layer.objects.active = armature

                # Select all bones inside the armature
                bpy.ops.object.mode_set(mode='POSE')  # Ensure we're in Pose Mode
                bpy.ops.pose.select_all(action='SELECT')

                for bone in armature.pose.bones:
                    print("Found bone: " + bone.name)
                    bone.bone.select = True  # Select each bone
                    
                bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to Object Mode

            # Export the selected objects
            bpy.ops.export_scene.fbx(
                filepath=fileName,
                check_existing=True,
                axis_forward='Y',
                axis_up='Z',
                use_selection=True,
                global_scale=1.0,
                apply_unit_scale=True,
                bake_space_transform=False,  # Prevent hierarchy collapse
                object_types={'MESH', 'ARMATURE'},
                use_mesh_modifiers=True,
                mesh_smooth_type='EDGE',
                use_tspace=True,
                use_custom_props=False,
                add_leaf_bones=False,  # Prevent extra bones
                primary_bone_axis='Y',
                secondary_bone_axis='X',
                use_armature_deform_only=True,  # Keep all bones
                armature_nodetype='NULL',
                path_mode='AUTO',
                embed_textures=False,
                batch_mode='OFF',
                use_metadata=True,
                apply_scale_options='FBX_SCALE_NONE',
            )

            
                                        
            view_layer.objects.active = None

            generatedFBXFiles.append(filePath + "\\" + fbxName)

            bpy.ops.object.select_all(action='DESELECT')

            print ("Exported: %s"%fileName)

        content_file = content_root + f"\{collection_name}_content.mgcb"
        print("CONTENT FILE: " + content_file)
        with open(content_file, "w") as file:

            file.write("/outputDir:bin/Windows\n")
            file.write("/intermediateDir:obj/Windows\n")
            file.write("/platform:Windows\n")
            file.write("/config:\n")
            file.write("/profile:HiDef\n")
            file.write("/compress:False\n\n")

            for generatedFile in generatedFBXFiles:
                model_path = safe_relative_path(generatedFile, content_root)
                file.write(f"#begin {model_path}\n")
                file.write("/importer:FbxImporter\n")
                file.write("/processor:ModelProcessor\n")
                file.write("/processorParam:ColorKeyColor=0,0,0,0\n")
                file.write("/processorParam:ColorKeyEnabled=True\n")
                file.write("/processorParam:DefaultEffect=BasicEffect\n")
                file.write("/processorParam:GenerateMipmaps=True\n")
                file.write("/processorParam:GenerateTangentFrames=False\n")
                file.write("/processorParam:PremultiplyTextureAlpha=True\n")
                file.write("/processorParam:PremultiplyVertexColors=True\n")
                file.write("/processorParam:ResizeTexturesToPowerOfTwo=False\n")
                file.write("/processorParam:RotationX=0\n")
                file.write("/processorParam:RotationY=0\n")
                file.write("/processorParam:RotationZ=0\n")
                file.write("/processorParam:Scale=1\n")
                file.write("/processorParam:SwapWindingOrder=False\n")
                file.write("/processorParam:TextureFormat=DxtCompressed\n")
                file.write(f"/build:{model_path}\n\n")

    


# The load handler will trigger the export
@persistent
def load_handler(dummy):
    print("Load Handler:", bpy.data.filepath)

    path, filename = os.path.split(bpy.data.filepath)

    targetPath = os.path.dirname(destinationPath)
    targetFile = os.path.join(targetPath, filename.replace(".blend", ".fbx"))

    if not os.path.exists(targetPath):
        os.mkdir(targetPath)

    print("Starting export: %s"%targetPath)
    doExport(targetPath)

# Install the load handler
bpy.app.handlers.load_post.append(load_handler)

# Open the .blend file
bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)