<!--
  - Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
  - Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
  - BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
  -
  - License for BK-LOG 蓝鲸日志平台:
  - -------------------------------------------------------------------
  -
  - Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
  - documentation files (the "Software"), to deal in the Software without restriction, including without limitation
  - the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
  - and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
  - The above copyright notice and this permission notice shall be included in all copies or substantial
  - portions of the Software.
  -
  - THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
  - LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
  - NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
  - WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  - SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
  -->

<template>
  <div class="step-result-wrapper">
    <div class="step-result-container">
      <i class="bk-icon icon-check-circle"></i>
      <h3 class="title">{{ finishText }}</h3>
      <!-- <p v-if="host.count"> -->
      <!-- <p class="info">
                {{ '共' }}<span class="host-number text-primary">{{ host.count || 0 }}</span>{{ '台主机' }}
                <template>{{ '，成功' }}
                  <span class="host-number text-success">{{ host.success || 0 }}</span>{{ '台主机' }}</template>
                <template>{{ '，失败' }}
                  <span class="host-number text-failed">{{ host.failed || 0 }}</span>{{ '台主机' }}</template>
            </p> -->
      <div class="result-button-group">
        <bk-button @click="routeChange('complete')">{{ $t('dataManage.Return_list') }}</bk-button>
        <bk-button theme="primary" @click="routeChange('search')">{{ $t('dataManage.To_retrieve') }}</bk-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'step-result',
  props: {
    operateType: String,
    isSwitch: Boolean,
    indexSetId: {
      type: [String, Number],
      default: '',
    },
    type: {
      type: String,
      default: 'create',
    },
    host: {
      type: Object,
      default() {
        return {};
      },
    },
  },
  data() {
    return {
      finish: {
        add: this.$t('dataManage.add'),
        edit: this.$t('dataManage.edit'),
        editFinish: this.$t('dataManage.editFinish'),
        field: this.$t('dataManage.field'),
        start: this.$t('dataManage.start'),
        stop: this.$t('dataManage.stop'),
      },
    };
  },
  computed: {
    // title () {
    //     const titleText = {
    //         add: '采集配置创建完成',
    //         edit: '采集配置修改完成',
    //         start: '启用采集配置任务完成',
    //         stop: '停用采集配置任务完成'
    //     }
    //     return titleText[this.operateType]
    // }
    finishText() {
      return this.finish[this.operateType];
    },
  },
  methods: {
    routeChange(type) {
      let routeName = 'collectAccess';
      if (type === 'search' || type === 'clear') {
        routeName = 'retrieve';
      }
      this.$router.replace({
        name: routeName,
        params: {
          indexId: type === 'search' && this.indexSetId ? this.indexSetId : '',
        },
        query: {
          projectId: window.localStorage.getItem('project_id'),
        },
      });
    },
  },
};
</script>

<style lang="scss">
  @import '../../scss/conf';

  .step-result-wrapper {
    position: relative;
    padding-top: 105px;

    .step-result-container {
      width: 500px;
      margin: 0 auto;
      text-align: center;

      .icon-check-circle {
        font-size: 56px;
        color: $successColor;
      }

      .title {
        margin: 21px 0 0 0;
        padding: 0;
        font-size: 16px;
        color: #000;
      }

      .info {
        margin-top: 10px;
        font-size: 12px;
        color: #6e7079;
      }

      .host-number {
        margin: 0 3px;
      }

      .text-primary {
        color: $primaryColor;
      }

      .text-success {
        color: $successColor;
      }

      .text-failed {
        color: $failColor;
      }
    }

    .result-button-group {
      margin-top: 36px;
      font-size: 0;

      .bk-button + .bk-button {
        margin-left: 10px;
      }
    }
  }
</style>
