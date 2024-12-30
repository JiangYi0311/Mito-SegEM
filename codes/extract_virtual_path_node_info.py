import numpy as np
from tqdm import tqdm
import webknossos as wk
import fastremap
import os, h5py
import cv2
from tifffile import imwrite, imread
import pandas as pd
from collections import Counter
from PIL import Image

def dict_merge(dict1, dict2):
    return dict(Counter(dict1) + Counter(dict2))

def read_excel_to_dict(path):
    df = pd.read_excel(path)
    data = df.set_index('id')['volume(um3)'].to_dict()
    return data
    
def read_csv_to_dict(path):
    df = pd.read_csv(path)
    data = df.set_index('id')['volume(um3)'].to_dict()
    return data

def calculate_segment_volume(Auth_Token, ANNOTATION_URL, LAYER_NAME, BBOX):
    with wk.webknossos_context(token=Auth_Token, url="your ip address"):
        dataset = wk.Annotation.open_as_remote_dataset(annotation_id_or_url=ANNOTATION_URL)
        voxel_size = np.array(dataset.voxel_size)
        voxel_size_in_um3 = voxel_size[0] * voxel_size[1] * voxel_size[2] / (1000*1000*1000) # nm --> um
        # annotation = wk.Annotation.download(ANNOTATION_URL)
        mag_view = dataset.get_layer(layer_name=LAYER_NAME).get_finest_mag()
        dict_id_count = {}
        with mag_view.get_buffered_slice_reader(absolute_bounding_box=BBOX, buffer_size=20) as reader:
            for slice_data in tqdm(reader):
                stats_per_id = {}
                uniques, counts = fastremap.unique(slice_data, return_counts=True)
                for _id, count in zip(uniques, counts):
                    if _id == 0:
                        continue
                    stats_per_id[_id] = count
                dict_id_count = dict_merge(dict_id_count, stats_per_id)
            for key in dict_id_count:
                dict_id_count[key] *= voxel_size_in_um3
    return dict_id_count


def extract_skeleton_nodes(auth_token, annotation_url, LAYER_NAME, BBOX, save_path_excel, csv_path, read_csv=True, whether_Group):
    with wk.webknossos_context(token=auth_token, url="your ip address"):
        print("#####start extracting segmentation#####")
        # segmentation
        dataset = wk.Annotation.open_as_remote_dataset(annotation_id_or_url=annotation_url)
        mag_view = dataset.get_layer(layer_name=LAYER_NAME).get_finest_mag()

        print("#####start extracting the skeleton#####")
        # skeleton
        nml_annotation = wk.Annotation.download(annotation_url)
        nml_skeleton = nml_annotation.skeleton
        voxel_size = nml_annotation.voxel_size
        
        if read_csv is True:
            print("#####from csv file read id and volume#####")
            id_volume_dict = read_csv_to_dict(csv_path)
            print("mito number:", len(id_volume_dict))
        else:
            print("#####start calculating the volume of the segments#####")
            # volume
            id_volume_dict = calculate_segment_volume(auth_token, annotation_url, LAYER_NAME, BBOX)  # BBOX segmentation boundingbox
            print("mito number:", len(id_volume_dict))
            df_0 = pd.DataFrame(id_volume_dict.items(), columns=["id", "volume(um3)"])
            df_0.to_csv(os.path.join(save_path_excel, 'mito_id_volume.csv'), index=False)
        
        if whether_Group is True:
            # Group --> tree
            print("#####Start calculating the corresponding id and volume of the nodes#####")
            for group in tqdm(nml_skeleton.flattened_groups()):
                if group.name.split("-")[0] in ["mito"]:  # extract the specified group
                    print(group.name)
                    excel_path = os.path.join(save_path_excel, group.name + '.xlsx')
                    with pd.ExcelWriter(excel_path) as writer:
                        for tree in group.flattened_trees():
                            segment_id_mapping = {}
                            node_coord = {}
                            node_coord_list = []
                            for node in tree.nodes:
                                segment_id = mag_view.read(absolute_offset=node.position, size=(1, 1, 1)).item()
                                if segment_id == 0:
                                    continue
                                if segment_id not in id_volume_dict.keys():
                                    continue
                                # Only one point is extracted for multiple points on the individual mitochondrial instance
                                segment_id_mapping[segment_id] = id_volume_dict[segment_id]
                                node_coord[segment_id] = [node.position[0], node.position[1], node.position[2]]
                            node_coord_list.extend(node_coord.values())
                            print(group.name, tree.name)
                            df = pd.DataFrame(segment_id_mapping.items(), columns=["id", "volume(um3)"])
                            df_coord = pd.DataFrame(node_coord_list, columns=["X", "Y", "Z"])
                            df = pd.concat([df, df_coord], axis=1)
                            df.to_excel(writer, sheet_name=tree.name, index=False)
        else:
            # tree
            print("#####Start calculating the corresponding id and volume of the nodes#####")
            excel_path = os.path.join(save_path_excel, 'mito_volume_Cell' + '.xlsx')
            with pd.ExcelWriter(excel_path) as writer:
                for tree in nml_skeleton.flattened_trees():
                    if tree.name.split("-")[0] in ["mito"]:  # select specific tree
                        segment_id_mapping = {}
                        node_coord = {}
                        node_coord_list = []
                        for node in tree.nodes:
                            segment_id = mag_view.read(absolute_offset=node.position, size=(1, 1, 1)).item()
                            if segment_id == 0:
                                continue
                            if segment_id not in id_volume_dict.keys():
                                continue
                            # Only one point is extracted for multiple points on the individual mitochondrial instance
                            segment_id_mapping[segment_id] = id_volume_dict[segment_id]
                            node_coord[segment_id] = [node.position[0], node.position[1], node.position[2]]
                        node_coord_list.extend(node_coord.values())
                        print(tree.name)
                        df = pd.DataFrame(segment_id_mapping.items(), columns=["id", "volume(um3)"])
                        df_coord = pd.DataFrame(node_coord_list, columns=["X", "Y", "Z"])  # coordinate of point in webknossos
                        df = pd.concat([df, df_coord], axis=1)
                        df.to_excel(writer, sheet_name=tree.name, index=False)

                   
if __name__ == "__main__":

    Auth_Token = ""  # unique Token for each user in webknossos
    ID_ANNOTATION = ""  # unique ID for each project in webknossos
    ANNOTATION_ID_OR_URL = "your ip address/annotations/{}".format(ID_ANNOTATION)
    LAYER_NAME = "segmentation"  # layer in webknossos
    x_0, y_0, z_0, X, Y, Z = 0, 0, 0, 10000, 10000, 2000  # dataset size in webknossos
    BBOX = wk.BoundingBox((x_0, y_0, z_0), (X, Y, Z))

    save_path_excel = ""  # save path, mitochondrial ids were saved to excel
    os.makedirs(save_path_excel, exist_ok=True)

    csv_path = ""  # mitochondrial volume was precomputed and saved to a csv file.
    read_csv = True  # True, volume was precomputed. False, volume was not precomputed.
    whether_Group = False  # True, trees were grouped. False, trees were not grouped.
    extract_skeleton_nodes(Auth_Token, ANNOTATION_ID_OR_URL, LAYER_NAME, BBOX, save_path_excel, csv_path, read_csv, whether_Group)

