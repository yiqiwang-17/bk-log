/*
 * Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
 * Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
 * BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
 *
 * License for BK-LOG 蓝鲸日志平台:
 * --------------------------------------------------------------------
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
 * documentation files (the "Software"), to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
 * and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all copies or substantial
 * portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
 * LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
 * NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
 * SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

export const stepsConf = {
  // 采集新增或编辑未完成，itsm
  itsm: [
    { title: global.mainComponent.$t('采集配置'), icon: '' },
    { title: global.mainComponent.$t('容量评估'), icon: '' },
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('字段提取&存储'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],

  // 采集新增
  add: [
    { title: global.mainComponent.$t('采集配置'), icon: '' },
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('字段提取&存储'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
  // 采集修改
  edit: [
    { title: global.mainComponent.$t('采集配置'), icon: '' },
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('字段提取&存储'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
  // 采集修改
  editFinish: [
    { title: global.mainComponent.$t('采集配置'), icon: '' },
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('字段提取&存储'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
  // 字段提取
  field: [
    { title: global.mainComponent.$t('采集配置'), icon: '' },
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('字段提取&存储'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
  // 开始采集
  start: [
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
  // 停止采集
  stop: [
    { title: global.mainComponent.$t('采集下发'), icon: '' },
    { title: global.mainComponent.$t('完成'), icon: '' },
  ],
};

export const finishRefer = {
  add: 4,
  edit: 4,
  editFinish: 4,
  field: 4,
  start: 2,
  stop: 2,
};
