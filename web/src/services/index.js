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

import * as userInfo from './userInfo';
import * as example from './example';
import * as retrieve from './retrieve';
import * as source from './source';
import * as indexSet from './indexSet';
import * as meta from './meta';
import * as monitor from './monitor';
import * as auth from './auth';
import * as plugins from './plugins';
import * as resultTables from './resultTables';
import * as biz from './biz';
import * as collect from './collect';
import * as particulars from './particulars';
import * as migrate from './migrate';
import * as traceDetail from './traceDetail';
import * as trace from './trace';
import * as extract from './extract';
import * as extractManage from './extractManage';
import * as linkConfiguration from './linkConfiguration';

const getMyProjectList = {
  url: '/meta/projects/mine/',
  method: 'get',
};

export default {
  userInfo,
  example,
  retrieve,
  project: {
    getMyProjectList,
  },
  indexSet,
  source,
  meta,
  monitor,
  auth,
  plugins,
  resultTables,
  biz,
  particulars,
  collect,
  migrate,
  traceDetail,
  trace,
  extract,
  extractManage,
  linkConfiguration,
};
