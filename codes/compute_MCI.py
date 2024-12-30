import numpy as np
import os
from PIL import Image
from tqdm import tqdm
from tifffile import imread, imwrite
from zmesh import Mesher
import vtk
import pandas as pd


def voxel_to_mesh(path, save_path, voxel_size, data_type=np.uint16):
    filename = sorted(os.listdir(path))
    N = len(filename)
    img = Image.open(os.path.join(path, filename[0]))
    w, h = img.size
    print("#####read image data#######")
    labels = np.empty((h, w, N), data_type)
    for i, name in tqdm(enumerate(filename)):
        labels[:, :, i] = imread(os.path.join(path, name))
    
    mesher = Mesher((voxel_size[0], voxel_size[1], voxel_size[2]))  # anisotropy of image
    print("creat mesh")
    mesher.mesh(labels, close=True)  # close=False,
    for obj_id in tqdm(mesher.ids()):
        mesh = mesher.get(obj_id)
        # Common binary format
        with open(os.path.join(save_path, str(obj_id).zfill(5) + '.ply'), 'wb') as f:
            f.write(mesh.to_ply())


def serial_file_voxel_to_mesh(path, save_path, voxel_size, data_type):
    filename = os.listdir(path)
    for name in filename:
        file_path = os.path.join(path, name)
        mesh_save_path = os.path.join(save_path, name)
        os.makedirs(mesh_save_path, exist_ok=True)
        voxel_to_mesh(file_path, mesh_save_path, voxel_size, data_type)


def from_ply_compute_volume_surface_area(path, save_path):
    filename = sorted(os.listdir(path))
    data_id_v_s = []
    for name in tqdm(filename):
        # read ply file
        reader = vtk.vtkPLYReader()
        reader.SetFileName(os.path.join(path, name))
        reader.Update()
        # caculate volume
        volume = vtk.vtkMassProperties()
        volume.SetInputData(reader.GetOutput())
        volume.Update()
        volume_ply = volume.GetVolume()
        # print("Volume:", volume.GetVolume())
        # caculate surface area
        surface_area = vtk.vtkMassProperties()
        surface_area.SetInputData(reader.GetOutput())
        surface_area.Update()
        surface_area_ply = surface_area.GetSurfaceArea()
        # print("Surface Area:", surface_area.GetSurfaceArea())
        mci_ply = (surface_area_ply ** 3)/((4 * np.pi * volume_ply)**2)  # MCI formula
        data_id_v_s.append([int(name.split(".")[0]), volume_ply, surface_area_ply, mci_ply])

    df_id_v_s = pd.DataFrame(data_id_v_s, columns=["id", "volume", "surface_area", "MCI"])
    df_id_v_s.to_excel(save_path, index=False)

def serial_file_from_ply_compute_volume_surface_area(path, save_path):
    filename = os.listdir(path)
    for name in filename:
        file_path = os.path.join(path, name)
        mesh_save_path = os.path.join(save_path, name + '.xlsx')
        # os.makedirs(mesh_save_path, exist_ok=True)
        from_ply_compute_volume_surface_area(file_path, mesh_save_path)

if __name__ == "__main__":

    # first step
    # image to mesh
    path = ""  # image path
    save_path = ""  # mesh save path
    os.makedirs(save_path, exist_ok=True)
    voxel_size = [15, 15, 40]
    data_type = np.uint32  # image dtype np.uint8, np.uint16, np.uint32
    serial_file_voxel_to_mesh(path, save_path, voxel_size, data_type)

    """
    # second step
    # mesh to volume, surface, MCI
    path = ""  # mesh path
    save_path = ""  # mesh_statistics volume surface MCI
    os.makedirs(save_path, exist_ok=True)
    serial_file_from_ply_compute_volume_surface_area(path, save_path)
    """


    
    



