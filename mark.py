# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@contact: JHC000abc@gmail.com
@file: mark_image.py
@time: 2023/01/14/ 20:58
@desc:不上传可以不导入这个from Project.util import bos_util，这是基于bos封装的自定义工具包，会报错，相关代码删掉就行
"""
import os
import json
from PIL import ImageFont, Image, ImageDraw
import cv2 as cv
import numpy as np
# from Project.util import bos_util


class MarkImage():

    def __init__(self):
        self.bos_client = bos_util.get_bos_client()
        # 是否标注文字
        self.TEXT = True
        # 是否标注方框
        self.BOX = True
        # 是否标注文字索引
        self.INDEX = True
        # 标注文字大小
        self.SIZE = 20
        # 是否旋转
        self.TRANSPOSE = False
        # 标注字体格式
        self.Font = R'C:\\Windows\\Fonts\\simkai.ttf'
        # 标注颜色
        self.COLOR = (0, 0, 255)
        # 标注线粗
        self.THICKNESS = 2
        # bos路径唯一标识符
        self.SINGLE = "MarkImage"
        # # 是否上传处理结果到bos
        # self.UPLOAD = True

    def save_log(self, file, text):
        """
        保存日志
        :param file:
        :param text:
        :return:
        """
        with open(file, "a", encoding="utf-8")as fp:
            fp.write("{}\n".format(text))

    # def upload(self, file, retry=3):
    #     """
    #     上传
    #     :param file:
    #     :param retry:
    #     :return:
    #     """
    #     source_bucket = 'collection-data'
    #     bos_file = "/jiaohaicheng/{}/{}".format(
    #         self.SINGLE, "/".join(file.split("\\")[-3:]))
    #     status = False
    #     while not status and retry > 0:
    #         try:
    #             if self.UPLOAD:
    #                 bos_util.upload_file(
    #                     self.bos_client, source_bucket, bos_file, file)
    #                 status = True
    #             else:
    #                 retry = 0
    #         except Exception as e:
    #             print(e,e.__traceback__.tb_lineno)
    #             retry -= 1
    #
    #     if not status:
    #         if self.UPLOAD:
    #             return "Error Upload File : "+"https://bj.bcebos.com/collection-data" + bos_file
    #         else:
    #             return file
    #     else:
    #         if self.UPLOAD:
    #             return "https://bj.bcebos.com/collection-data" + bos_file

    def transpose(self, image, key: int):
        """
        旋转,逆时针
        """
        return image.rotate(key)

    def read_image(self, file, key=0):
        """
        读取图像,带旋转功能
        :param file:
        :param key:
        :return:
        """
        img = Image.open(file).convert('RGB')
        if self.TRANSPOSE:
            img = self.transpose(img, key)
        img = np.asarray(img)
        return img

    def save_img(self, img, file, name=".jpg"):
        """
        保存图像到本地
        :param img:
        :param file:
        :param name:
        :return:
        """
        cv.imencode(name, img)[1].tofile(file)

    def draw_polygon(self, img, opt_lis):
        """
        标注框
        :param img:图像 numpy
        :param opt_lis: 标注位置坐标
        :return:
        """
        if self.BOX:
            if len(opt_lis) != 2:
                pts = np.array(opt_lis, dtype=np.int32)
                cv.polylines(img,
                             [pts],
                             True,
                             self.COLOR,
                             self.THICKNESS
                             )
            else:
                cv.rectangle(
                    img,
                    tuple(opt_lis[0]),
                    tuple(opt_lis[1]),
                    color=self.COLOR,
                    thickness=self.THICKNESS

                )

    def calculate_max_opt(self, opt):
        """
        计算最大横纵坐标,横坐标加上偏移量(字体大小的1/5)
        :param opt: [[,],[,]]
        :return:
        """
        max_x = []
        max_y = []
        for i in opt:
            if len(i) == 2:
                max_x.append(i[0])
                max_y.append(i[1])
        return max(max_x) + self.SIZE / 5, max(max_y) - self.SIZE / 5

    def add_words_on_pic(self, opt, index, text, image):
        """
        添加文字
        :param opt: tuple (,)
        :param index: 标注文本序号
        :param text: 标注文本
        :param image: 图像 ,numpy
        :return:
        """
        _text = ""
        if self.INDEX:
            _text = str(index)
            if self.TEXT:
                _text = _text + "." + text
        else:
            if self.TEXT:
                _text = text
        try:
            font = ImageFont.truetype(self.Font, size=self.SIZE)
            img_PIL = Image.fromarray(image)
            draw = ImageDraw.Draw(img_PIL)
            draw.text(xy=(opt[0], opt[1] - (self.SIZE / 2)),
                      text=_text, font=font, fill=(0, 0, 255))
            image = cv.cvtColor(np.asarray(img_PIL), cv.COLOR_RGB2RGBA)
        except Exception as e:
            print("add_words_on_pic error", e, e.__traceback__.tb_lineno)
        return image

    def process(self, file, map_lis, save_file):
        """
        图像处理流程
        :param file:图像位置
        :param map_lis: 标注坐标[1:{opt:value}]
        :param id: 标注文本序号
        :param text: 标注文本
        :param save_file: 图像存储位置
        :return:
        """
        try:
            # 读取图像
            img = self.read_image(file)
            for index,value in map_lis.items():
                # 标注框
                self.draw_polygon(img, value["opt"])
                # 计算文本标注位置(x最大值+偏移量,y最大值-偏移量)
                opt = self.calculate_max_opt(value["opt"])
                # 标注文字
                img = self.add_words_on_pic(opt=opt, index=index, text=value["text"], image=img)
            # 保存图像
            self.save_img(img, save_file)
            # bos_file_status:上传状态,成功只返回bos路径,若失败,路径前有error upload file : 标识,未开启上传功能,返回本地待上传图片路径
            bos_file_status = self.upload(save_file)
            print(bos_file_status)
        except Exception as e:
            print("Process {} Error : ".format(file),e,e.__traceback__.tb_lineno)

    # def get_info(self,file):
    #     with open(file,"r",encoding="utf-8")as fp:
    #         header = fp.readline()
    #         for i in fp:


if __name__ == '__main__':
    mi = MarkImage()
    file = R"E:\Desktop\20170427101835143.png"
    save_path = R"F:\BaiduCodingSpace\SupportRequirements\Project\image\mark"
    img_name = os.path.split(file)[-1]
    os.makedirs(save_path, exist_ok=True)
    save_file = os.path.join(save_path, img_name)

    map_lis = {
        1:{
            "opt":[
                [100, 200],
                [130, 210],
                [135, 282],
                [100, 260],
            ],
            "text":"中国"
        },
        2:{
            "opt": [
                [200, 200],
                [230, 210],
                [235, 282],
                [200, 260],
            ],
            "text":"日本"
        }
    }
    mi.process(file, map_lis, save_file)