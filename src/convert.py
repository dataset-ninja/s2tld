import glob
import os
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlparse

import supervisely as sly
from dataset_tools.convert import unpack_if_archive
from supervisely.io.fs import get_file_name, get_file_name_with_ext
from tqdm import tqdm

import src.settings as s


def download_dataset(teamfiles_dir: str) -> str:
    """Use it for large datasets to convert them on the instance"""
    api = sly.Api.from_env()
    team_id = sly.env.team_id()
    storage_dir = sly.app.get_data_dir()

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, str):
        parsed_url = urlparse(s.DOWNLOAD_ORIGINAL_URL)
        file_name_with_ext = os.path.basename(parsed_url.path)
        file_name_with_ext = unquote(file_name_with_ext)

        sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
        local_path = os.path.join(storage_dir, file_name_with_ext)
        teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

        fsize = api.file.get_directory_size(team_id, teamfiles_dir)
        with tqdm(
            desc=f"Downloading '{file_name_with_ext}' to buffer...",
            total=fsize,
            unit="B",
            unit_scale=True,
        ) as pbar:
            api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)
        dataset_path = unpack_if_archive(local_path)

    if isinstance(s.DOWNLOAD_ORIGINAL_URL, dict):
        for file_name_with_ext, url in s.DOWNLOAD_ORIGINAL_URL.items():
            local_path = os.path.join(storage_dir, file_name_with_ext)
            teamfiles_path = os.path.join(teamfiles_dir, file_name_with_ext)

            if not os.path.exists(get_file_name(local_path)):
                fsize = api.file.get_directory_size(team_id, teamfiles_dir)
                with tqdm(
                    desc=f"Downloading '{file_name_with_ext}' to buffer...",
                    total=fsize,
                    unit="B",
                    unit_scale=True,
                ) as pbar:
                    api.file.download(team_id, teamfiles_path, local_path, progress_cb=pbar)

                sly.logger.info(f"Start unpacking archive '{file_name_with_ext}'...")
                unpack_if_archive(local_path)
            else:
                sly.logger.info(
                    f"Archive '{file_name_with_ext}' was already unpacked to '{os.path.join(storage_dir, get_file_name(file_name_with_ext))}'. Skipping..."
                )

        dataset_path = storage_dir
    return dataset_path


def count_files(path, extension):
    count = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(extension):
                count += 1
    return count


def convert_and_upload_supervisely_project(
    api: sly.Api, workspace_id: int, project_name: str
) -> sly.ProjectInfo:
    ### Function should read local dataset and upload it to Supervisely project, then return project info.###
    big_images_path = "/home/alex/DATASETS/TODO/S2TLD/S2TLD（1080x1920）/JPEGImages"
    small_images_path = "/home/alex/DATASETS/TODO/S2TLD/S2TLD（720x1280）"
    bboxes_path = "/home/alex/DATASETS/TODO/S2TLD/S2TLD（1080x1920）/Annotations"
    batch_size = 30
    ds_name = "ds"

    ann_ext = ".xml"

    def create_ann(image_path):
        labels = []
        tags = []

        res = image_path.split("1080x1920")
        if len(res) > 1:
            resolution = sly.Tag(resolution_big)
        else:
            resolution = sly.Tag(resolution_small)
            norm = image_path.split("normal_1")
            if len(norm) > 1:
                normal = sly.Tag(n1_meta)
            else:
                normal = sly.Tag(n2_meta)
            tags.append(normal)
        tags.append(resolution)

        ann_path = image_path.replace("JPEGImages", "Annotations").replace(".jpg", ".xml")

        tree = ET.parse(ann_path)
        root = tree.getroot()

        img_wight = int(root.find(".//width").text)
        img_height = int(root.find(".//height").text)

        objects_content = root.findall(".//object")
        for obj_data in objects_content:
            name = obj_data.find(".//name").text
            obj_class = meta.get_obj_class(name)
            bndbox = obj_data.find(".//bndbox")
            top = int(bndbox.find(".//ymin").text)
            left = int(bndbox.find(".//xmin").text)
            bottom = int(bndbox.find(".//ymax").text)
            right = int(bndbox.find(".//xmax").text)

            rect = sly.Rectangle(left=left, top=top, right=right, bottom=bottom)
            label = sly.Label(rect, obj_class)
            labels.append(label)

        return sly.Annotation(img_size=(img_height, img_wight), labels=labels, img_tags=tags)

    red = sly.ObjClass("red", sly.Rectangle)
    yellow = sly.ObjClass("yellow", sly.Rectangle)
    green = sly.ObjClass("green", sly.Rectangle)
    off = sly.ObjClass("off", sly.Rectangle)
    wait_on = sly.ObjClass("wait_on", sly.Rectangle)

    resolution_big = sly.TagMeta("1080x1920", sly.TagValueType.NONE)
    resolution_small = sly.TagMeta("720x1280", sly.TagValueType.NONE)

    n1_meta = sly.TagMeta("normal 1", sly.TagValueType.NONE)
    n2_meta = sly.TagMeta("normal 2", sly.TagValueType.NONE)

    project = api.project.create(workspace_id, project_name, change_name_if_conflict=True)
    meta = sly.ProjectMeta(
        obj_classes=[red, yellow, green, off, wait_on],
        tag_metas=[resolution_big, resolution_small, n1_meta, n2_meta],
    )
    api.project.update_meta(project.id, meta.to_json())

    dataset = api.dataset.create(project.id, ds_name, change_name_if_conflict=True)

    big_images_pathes = glob.glob(big_images_path + "/*.jpg")
    small_images_pathes = glob.glob(small_images_path + "/*/*/*.jpg")

    all_images = big_images_pathes + small_images_pathes

    progress = sly.Progress("Create dataset {}".format(ds_name), len(all_images))

    for img_pathes_batch in sly.batched(all_images, batch_size=batch_size):
        img_names_batch = [get_file_name_with_ext(im_path) for im_path in img_pathes_batch]

        img_infos = api.image.upload_paths(dataset.id, img_names_batch, img_pathes_batch)
        img_ids = [im_info.id for im_info in img_infos]

        anns = [create_ann(image_path) for image_path in img_pathes_batch]
        api.annotation.upload_anns(img_ids, anns)

        progress.iters_done_report(len(img_names_batch))

    return project
