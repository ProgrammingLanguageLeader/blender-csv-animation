import os
import csv
import math

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, FloatProperty

bl_info = {
    "name": "Export > CSV Animation Exporter (.csv)",
    "author": "Dmitry Shorokhov",
    "version": (2, 5, 1),
    "blender": (2, 6, 3),
    "api": 36079,
    "location": "File > Export > CSV Animation Exporter (.csv)",
    "description": "Export > CSV Animation Exporter (.csv)",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}


class ExportCsv(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.folder"
    bl_label = "Export"
    filename_ext = ''
    use_filter_folder = True

    filepath = StringProperty(
        name="File Path",
        description="File path used for exporting CSV files",
        maxlen=1024,
        subtype='DIR_PATH',
        default=""
    )

    def execute(self, context):
        export_animation(context, self.filepath)
        return {'FINISHED'}


def export_animation(context, folder_path):
    create_folder_if_does_not_exist(folder_path)
    scene = context.scene
    objects = context.visible_objects
    frame_start = scene.frame_start
    frame_end = scene.frame_end
    for obj in objects:
        with open(
            os.path.join(
                folder_path, '{}.csv'.format(obj.name.lower())
            ), 'w'
        ) as csv_file:
            animation_file_writer = csv.writer(
                csv_file,
                delimiter=',',
                quotechar='|',
                quoting=csv.QUOTE_MINIMAL
            )
            prev_x, prev_y, prev_z = 0, 0, 0
            for frame_number in range(frame_start, frame_end + 1):
                scene.frame_set(frame_number)
                rgb = get_rgb_from_object(obj)
                world_matrix = obj.matrix_world.copy()
                translation_matrix = world_matrix.to_translation()
                x, y, z = translation_matrix[:]
                speed = calc_speed(
                    (x, y, z),
                    (prev_x, prev_y, prev_z)
                ) if frame_number != frame_start else 1
                if speed > 3:
                    bpy.context.window_manager.popup_menu(
                        popup_speed_error_menu,
                        title="Error",
                        icon='ERROR'
                    )
                prev_x, prev_y, prev_z = x, y, z
                animation_file_writer.writerow([
                    str(frame_number),
                    x, y, z,
                    speed,
                    *rgb,
                    str(obj.rotation_euler.z),
                ])
    return {'FINISHED'}


def create_folder_if_does_not_exist(folder_path):
    if os.path.isdir(folder_path):
        return
    os.mkdir(folder_path)


def get_rgb_from_object(obj):
    rgb = [0, 0, 0]
    try:
        if len(obj.data.materials) >= 1:
            material = obj.data.materials[0]
            for component in range(3):
                rgb[component] = int(material.diffuse_color[component] * 255)
    except AttributeError:
        pass
    finally:
        return rgb


def menu_func(self, context):
    self.layout.operator(
        ExportCsv.bl_idname,
        text="CSV Animation Exporter (.csv)"
    )


def register():
    bpy.utils.register_class(ExportCsv)
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.utils.unregister_class(ExportCsv)
    bpy.types.INFO_MT_file_export.remove(menu_func)


def calc_speed(start_point, end_point):
    time_delta = 0.1
    distance = math.sqrt(
        (start_point[0] - end_point[0]) ** 2 +
        (start_point[1] - end_point[1]) ** 2 +
        (start_point[2] - end_point[2]) ** 2
    )
    return distance / time_delta


def popup_speed_error_menu(self, context):
    self.layout.label("Speed is greater than 3 m/s")


if __name__ == "__main__":
    register()
