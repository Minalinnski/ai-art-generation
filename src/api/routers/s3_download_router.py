from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import boto3
import os
from zipfile import ZipFile
import uuid
import logging

router = APIRouter()
s3_client = boto3.client("s3")

@router.get("/download-s3-folder")
def download_s3_folder(
    bucket: str = Query(...),
    prefix: str = Query(...)
):
    # 生成唯一的任务ID
    # task_id = str(uuid.uuid4())
    task_id = prefix.split('/')[-2]
    
    # 创建本地临时目录
    temp_dir = f"tmp/{task_id}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # S3文件下载到本地
        paginator = s3_client.get_paginator("list_objects_v2")
        file_count = 0
        
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                
                # 跳过目录
                if key.endswith("/"):
                    continue
                
                # 计算本地文件路径
                rel_path = key[len(prefix):].lstrip('/')
                if not rel_path:  # 如果去掉prefix后是空的，使用原始key的文件名
                    rel_path = os.path.basename(key)
                
                local_path = os.path.join(temp_dir, rel_path)
                
                # 创建目录结构
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # 下载文件
                s3_client.download_file(bucket, key, local_path)
                file_count += 1
                logging.info(f"Downloaded: {key} -> {local_path}")
        
        if file_count == 0:
            raise HTTPException(status_code=404, detail="No files found")
        
        # 创建zip文件
        zip_path = os.path.join(temp_dir, "download.zip")
        with ZipFile(zip_path, "w") as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "download.zip":  # 跳过zip文件本身
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        logging.info(f"Created zip file: {zip_path}")
        logging.info(f"Temp directory: {temp_dir} (需要手动删除)")
        
        # return FileResponse(
        #     zip_path,
        #     filename="download.zip",
        #     media_type="application/zip"
        # )
        return {
            "status": "success",
            "file_path": zip_path
        }
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))