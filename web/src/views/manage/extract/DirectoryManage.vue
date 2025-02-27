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
  <div class="directory-manage-container">
    <div class="directory-manage">
      <div class="row-container">
        <div class="title">
          {{$t('用户组')}}
          <span class="required">*</span>
          <span class="log-icon icon-info-fill" v-bk-tooltips="{ width: 200, content: $t('不同类别的授权用户') }"></span>
        </div>
        <div class="content">
          <ValidateInput v-model.trim="manageStrategyData.strategy_name" style="width: 400px;"></ValidateInput>
        </div>
      </div>

      <div class="row-container">
        <div class="title">
          {{$t('用户列表')}}
          <span class="required">*</span>
          <span class="log-icon icon-info-fill" v-if="allowCreate"
                v-bk-tooltips="{ width: 200, content: $t('permission.tencentTips') }"></span>
          <span class="log-icon icon-info-fill" v-else
                v-bk-tooltips="{ width: 200, content: $t('permission.tips') }"></span>
        </div>
        <div class="content">
          <!-- <ValidateTagInput v-model.trim="manageStrategyData.user_list"
                        style="width: 400px;"
                        :list="users"
                        :allow-create="allowCreate"
                        :placeholder="allowCreate ? $t('form.pleaseEnterQQ') : ''"
                    ></ValidateTagInput> -->
          <ValidateUserSelector
            v-model="manageStrategyData.user_list"
            :api="userApi"
            :allow-create="allowCreate"
            :placeholder="allowCreate ? $t('form.pleaseEnterQQ') : ''">
          </ValidateUserSelector>
        </div>
      </div>

      <div class="row-container">
        <div class="title">
          {{$t('授权目录')}}
          <span class="required">*</span>
          <span class="log-icon icon-info-fill" v-bk-tooltips="{ width: 200, content: $t('授权目录提示') }"></span>
        </div>
        <div class="content">
          <div class="flex-box add-minus-component visible-dir"
               v-for="(item, index) in manageStrategyData.visible_dir" :key="index">
            <ValidateInput v-model.trim="manageStrategyData.visible_dir[index]"
                           style="width: 256px;margin-right: 4px;"
                           :validator="validateVisibleDir"
            ></ValidateInput>
            <span class="bk-icon icon-plus-circle" @click="handleAddVisibleDir"></span>
            <span class="bk-icon icon-minus-circle"
                  v-show="manageStrategyData.visible_dir.length > 1"
                  @click="manageStrategyData.visible_dir.splice(index, 1)"></span>
          </div>
        </div>
      </div>

      <div class="row-container">
        <div class="title">
          {{$t('文件后缀')}}
          <span class="required">*</span>
          <span class="log-icon icon-info-fill" v-bk-tooltips="$t('文件后缀提示')"></span>
        </div>
        <div class="content">
          <div
            class="flex-box add-minus-component file-type"
            v-for="(item, index) in manageStrategyData.file_type"
            :key="index">
            <ValidateInput
              v-model.trim="manageStrategyData.file_type[index]"
              style="width: 256px;margin-right: 4px;"
              :validator="validateFileExtension"
            ></ValidateInput>
            <span class="bk-icon icon-plus-circle" @click="handleAddFileType"></span>
            <span
              class="bk-icon icon-minus-circle"
              v-show="manageStrategyData.file_type.length > 1"
              @click="manageStrategyData.file_type.splice(index, 1)"></span>
          </div>
        </div>
      </div>

      <div class="row-container">
        <div class="title">
          {{$t('授权目标')}}
          <span class="required">*</span>
        </div>
        <div class="content">
          <div class="flex-box">
            <bk-button @click="showSelectDialog = true">+ {{$t('选择目标')}}</bk-button>
            <div class="select-text">
              {{$t('已选择')}}
              <span class="primary" v-if="manageStrategyData.modules.length">
                {{ manageStrategyData.modules.length }}
              </span>
              <span class="error" v-else>{{ manageStrategyData.modules.length }}</span>
              {{$t('个节点')}}
            </div>
          </div>
          <ModuleSelect :show-select-dialog.sync="showSelectDialog"
                        :selected-type="manageStrategyData.select_type"
                        :selected-modules="manageStrategyData.modules"
                        @confirm="handleConfirmSelect"></ModuleSelect>
        </div>
      </div>

      <div class="row-container">
        <div class="title">
          {{$t('执行人')}}
          <span class="required">*</span>
          <span class="log-icon icon-info-fill" v-bk-tooltips="{ width: 200, content: $t('执行人提示') }"></span>
        </div>
        <div class="content">
          <div class="flex-box">
            <bk-input readonly
                      style="width: 256px;margin-right: 10px;"
                      :value="manageStrategyData.operator"
                      :class="!manageStrategyData.operator && 'is-input-error'"
            ></bk-input>
            <bk-button :loading="isChangeOperatorLoading" @click="changeOperator">{{$t('改为我')}}</bk-button>
          </div>
        </div>
      </div>
    </div>
    <div class="button-container">
      <bk-button theme="primary" style="margin-right: 24px;" :disabled="!isValidated" @click="handleConfirm">
        {{$t('确认')}}
      </bk-button>
      <bk-button @click="handleCancel">
        {{$t('取消')}}
      </bk-button>
    </div>
  </div>
</template>

<script>
import ModuleSelect from './ModuleSelect';
import ValidateInput from './ValidateInput';
// import ValidateTagInput from './ValidateTagInput'
import ValidateUserSelector from './ValidateUserSelector.vue';

export default {
  components: {
    ModuleSelect,
    ValidateInput,
    // ValidateTagInput
    ValidateUserSelector,
  },
  props: {
    strategyData: {
      type: Object,
      default: {
        strategy_name: '',
        user_list: [],
        visible_dir: [''],
        file_type: [''],
        select_type: '',
        modules: [],
        operator: '',
      },
    },
    // users: {
    //     type: Array,
    //     required: true
    // },
    userApi: {
      type: String,
      required: true,
    },
    allowCreate: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    // 避免后台造的数据为空数组
    const strategyData = JSON.parse(JSON.stringify(this.strategyData));
    if (!strategyData.visible_dir?.length) {
      strategyData.visible_dir = [''];
    }
    if (!strategyData.file_type?.length) {
      strategyData.file_type = [''];
    }

    return {
      isChangeOperatorLoading: false,
      showSelectDialog: false,
      manageStrategyData: strategyData,
    };
  },
  computed: {
    isValidated() {
      return this.manageStrategyData.strategy_name
                    && this.manageStrategyData.user_list.length
                    && this.manageStrategyData.visible_dir.every(item => Boolean(this.validateVisibleDir(item)))
                    && this.manageStrategyData.file_type.every(item => Boolean(this.validateFileExtension(item)))
                    && this.manageStrategyData.modules.length
                    && this.manageStrategyData.operator;
    },
  },
  methods: {
    // 校验授权目录
    validateVisibleDir(val) {
      // 只允许：数字 字母 _-./
      // 不得出现 ./
      // 必须以 / 开头
      // 必须以 / 结尾
      // eslint-disable-next-line no-useless-escape
      return !/[^\w\-\.\/]/.test(val) && !/\.\//.test(val) && val.startsWith('/') && val.endsWith('/');
    },
    // 校验文件后缀
    validateFileExtension(val) {
      return !val.startsWith('.') && val;
    },
    handleAddVisibleDir() {
      this.manageStrategyData.visible_dir.push('');
      this.$nextTick(() => {
        const inputList = this.$el.querySelectorAll('.visible-dir input');
        inputList[inputList.length - 1].focus();
      });
    },
    handleAddFileType() {
      this.manageStrategyData.file_type.push('');
      this.$nextTick(() => {
        const inputList = this.$el.querySelectorAll('.file-type input');
        inputList[inputList.length - 1].focus();
      });
    },
    handleConfirmSelect(selectType, modules) {
      this.manageStrategyData.select_type = selectType;
      this.manageStrategyData.modules = modules;
    },
    async changeOperator() {
      const { operator } = this.$store.state.userMeta;
      if (operator) {
        this.manageStrategyData.operator = operator;
        return;
      }

      try {
        this.isChangeOperatorLoading = true;
        const res = await this.$http.request('userInfo/getUsername');
        this.$store.commit('updateUserMeta', res.data);
        this.manageStrategyData.operator = res.data.operator;
      } catch (e) {
        console.warn(e);
      } finally {
        this.isChangeOperatorLoading = false;
      }
    },
    handleCancel() {
      this.$emit('confirm', null);
    },
    handleConfirm() {
      this.$emit('confirm', this.manageStrategyData);
    },
  },
};
</script>

<style lang="scss" scoped>
  .directory-manage-container {
    position: relative;
    padding: 0 0 50px;
    height: calc(100vh - 60px);

    .directory-manage {
      height: 100%;
      padding: 0 0 20px;
      overflow: auto;

      .row-container {
        margin: 20px 24px 0;

        .title {
          font-size: 14px;
          line-height: 20px;
          margin-bottom: 8px;
          color: #313238;

          .required {
            font-size: 16px;
            color: #ff5656;
            font-weight: bold;
          }

          .icon-info-fill {
            color: #979ba5;
            cursor: pointer;
            font-size: 16px;
          }
        }

        .flex-box {
          display: flex;
          align-items: center;

          .select-text {
            margin-left: 12px;
            font-size: 14px;
            line-height: 16px;

            .primary {
              color: #3a84ff;
            }

            .error {
              color: #ea3636;
            }
          }

          .is-input-error.bk-form-control {
            /deep/ .bk-form-input {
              border-color: #ff5656 !important;
            }
          }
        }

        .add-minus-component {
          margin-bottom: 8px;

          .bk-icon {
            padding: 4px;
            color: #979ba5;
            font-size: 20px;
            cursor: pointer;
          }
        }
      }
    }

    .button-container {
      position: absolute;
      bottom: 0;
      padding-right: 24px;
      width: 100%;
      height: 50px;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      background: #fff;
      border-top: 1px solid #dcdee5;
    }
  }
</style>
