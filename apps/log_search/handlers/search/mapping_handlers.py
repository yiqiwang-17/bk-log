# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making BK-LOG 蓝鲸日志平台 available.
Copyright (C) 2021 THL A29 Limited, a Tencent company.  All rights reserved.
BK-LOG 蓝鲸日志平台 is licensed under the MIT License.
License for BK-LOG 蓝鲸日志平台:
--------------------------------------------------------------------
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import functools
import re
from collections import defaultdict

from typing import Dict, List, Any

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from apps.api import BkLogApi
from apps.log_search.constants import (
    BKDATA_ASYNC_FIELDS,
    BKDATA_ASYNC_CONTAINER_FIELDS,
    LOG_ASYNC_FIELDS,
    FEATURE_ASYNC_EXPORT_COMMON,
)
from apps.utils.cache import cache_one_hour
from apps.feature_toggle.handlers.toggle import FeatureToggleObject
from apps.utils.local import get_request_username
from apps.api import TransferApi, BkDataStorekitApi
from apps.log_search.exceptions import (
    SearchGetSchemaException,
    FieldsDateNotExistException,
    IndexSetNotHaveConflictIndex,
)
from apps.log_search.models import (
    LogIndexSet,
    ProjectInfo,
    Scenario,
    UserIndexSetConfig,
)
from apps.log_trace.handlers.trace_field_handlers import TraceFieldHandlers
from apps.utils.local import get_local_param
from apps.utils.time_handler import generate_time_range

INNER_COMMIT_FIELDS = ["dteventtime", "report_time"]
INNER_PRODUCE_FIELDS = [
    "dteventtimestamp",
    "dtEventTimeStamp",
    "_iteration_idx",
    "iterationIndex",
    "gseindex",
    "gseIndex",
    "timestamp",
]
OUTER_PRODUCE_FIELDS = []
TIME_TYPE = ["date"]
TRACE_SCOPE = ["trace", "trace_detail", "trace_detail_log"]
CONTEXT_SCOPE = ["search_context"]


class MappingHandlers(object):
    def __init__(
        self, indices, index_set_id, scenario_id, storage_cluster_id, time_field="", start_time="", end_time=""
    ):
        self.indices = indices
        self.index_set_id = index_set_id
        self.scenario_id = scenario_id
        self.storage_cluster_id = storage_cluster_id
        self.time_field = time_field
        self.start_time = start_time
        self.end_time = end_time
        self.time_zone: str = get_local_param("time_zone")

    def check_fields_not_conflict(self, raise_exception=True):
        if len(self.indices.split(",")) == 1:
            return True

        mapping_list: list = BkLogApi.mapping(
            {
                "indices": self.indices,
                "scenario_id": self.scenario_id,
                "storage_cluster_id": self.storage_cluster_id,
                "bkdata_authentication_method": "user",
            }
        )
        all_propertys = self._get_all_property(mapping_list)
        conflict_result = defaultdict(set)
        for property in all_propertys:
            self._get_sub_fields(conflict_result, property, "")
        have_conflict = {key: list(type_list) for key, type_list in conflict_result.items() if len(type_list) > 1}
        if have_conflict:
            if raise_exception:
                raise IndexSetNotHaveConflictIndex(data=have_conflict)
            return False

    def _get_sub_fields(self, conflict_result, properties, last_key):
        for property_key, property_define in properties.items():
            if "properties" in property_define:
                self._get_sub_fields(conflict_result, property_define["properties"], f"{last_key}.{property_key}")
                continue
            key = f"{last_key}.{property_key}" if last_key else property_key
            conflict_result[key].add(property_define["type"])

    def get_all_fields_by_index_id(self, scope="default"):
        mapping_list: list = self._get_mapping()
        property_dict: dict = self.find_megerd_property(mapping_list)
        fields_result: list = MappingHandlers.get_all_index_fields_by_mapping(property_dict)
        fields_list: list = [
            {
                "field_type": field["field_type"],
                "field_name": field["field_name"],
                "field_alias": field.get("field_alias"),
                "is_display": False,
                "is_editable": True,
                "tag": field.get("tag", "metric"),
                "es_doc_values": field.get("es_doc_values", False),
                "is_analyzed": field.get("is_analyzed", False),
            }
            for field in fields_result
        ]
        fields_list = self._combine_description_field(fields_list)
        # 针对trace场景进行description优化
        if scope in TRACE_SCOPE:
            fields_list = TraceFieldHandlers.trace_field_update(fields_list, scope)
        # 处理editable关系
        final_fields_list: list = self._combine_fields(fields_list)

        user_name = get_request_username()
        user_index_set_config_obj = UserIndexSetConfig.objects.filter(
            index_set_id=self.index_set_id, created_by=user_name, scope=scope
        ).first()

        # 用户已手动配置字段
        if user_index_set_config_obj:
            # 检查display_fields每个字段是否存在
            display_fields = user_index_set_config_obj.display_fields
            final_fields = [i["field_name"].lower() for i in final_fields_list]
            display_fields_list = [_filed_obj for _filed_obj in display_fields if _filed_obj.lower() in final_fields]

            for final_field in final_fields_list:
                field_name = final_field["field_name"]
                if field_name in display_fields_list:
                    final_field["is_display"] = True

            if scope in TRACE_SCOPE:
                # 增加trace内容优先逻辑
                display_fields_list = TraceFieldHandlers.trace_field_pop_up(display_fields_list, scope=scope)
            return final_fields_list, display_fields_list

        # trace链路
        if scope in TRACE_SCOPE:
            return final_fields_list, TraceFieldHandlers.get_trace_fieds(final_fields_list, scope)

        # search_context情况，默认只显示log字段
        if scope in CONTEXT_SCOPE:
            return self._get_context_fields(final_fields_list)

        # 其它情况
        display_fields_list = []
        if self.scenario_id == Scenario.ES:
            produce_fields = OUTER_PRODUCE_FIELDS
        elif self.scenario_id in [Scenario.BKDATA, Scenario.LOG]:
            produce_fields = INNER_PRODUCE_FIELDS
        else:
            produce_fields = list()
        range_num = len(final_fields_list) if len(final_fields_list) < 5 else 5
        for index_n in range(range_num):
            field_name = final_fields_list[index_n]["field_name"]
            if field_name not in produce_fields:
                final_fields_list[index_n]["is_display"] = True
                display_fields_list.append(field_name)
            else:
                final_fields_list[index_n]["is_display"] = False
        display_fields_list = self._sort_display_fields(display_fields_list)
        return final_fields_list, display_fields_list

    def _get_mapping(self):
        return self._get_latest_mapping(index_set_id=self.index_set_id)

    @cache_one_hour("latest_mapping_key_{index_set_id}")
    def _get_latest_mapping(self, *, index_set_id):  # noqa
        start_time, end_time = generate_time_range("1d", "", "", self.time_zone)
        latest_mapping = BkLogApi.mapping(
            {
                "indices": self.indices,
                "scenario_id": self.scenario_id,
                "storage_cluster_id": self.storage_cluster_id,
                "time_zone": self.time_zone,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        return latest_mapping

    @staticmethod
    def _get_context_fields(final_fields_list):
        for _field in final_fields_list:
            if _field["field_name"] == "log":
                _field["is_display"] = True
                return final_fields_list, ["log"]
        return final_fields_list, []

    @classmethod
    def get_all_index_fields_by_mapping(cls, properties_dict: Dict) -> List:
        """
        通过mapping集合获取所有的index下的fields
        :return:
        """
        fields_result: List = list()
        for key in properties_dict.keys():
            k_keys: list = properties_dict[key].keys()
            if "type" in k_keys:
                field_type: str = properties_dict[key]["type"]
                doc_values_farther_dict: dict = properties_dict[key]
                doc_values = False
                if isinstance(doc_values_farther_dict, dict):
                    doc_values = doc_values_farther_dict.get("doc_values", True)

                es_doc_values = doc_values
                if field_type in ["text", "object"]:
                    es_doc_values = False

                # @TODO tag：兼容前端代码，后面需要删除
                tag = "metric"
                if field_type == "date":
                    tag = "timestamp"
                elif es_doc_values:
                    tag = "dimension"

                data: Dict[str, Any] = dict()
                data.update(
                    {
                        "field_type": field_type,
                        "field_name": key,
                        "field_alias": "",
                        "description": "",
                        "es_doc_values": es_doc_values,
                        "tag": tag,
                        "is_analyzed": cls._is_analyzed(field_type),
                    }
                )
                fields_result.append(data)
                continue
            if "properties" in k_keys:
                fields_result.extend(cls.get_fields_recursively(p_key=key, properties_dict=properties_dict[key]))
                continue
        return fields_result

    @staticmethod
    def _is_analyzed(field_type: str):
        return field_type == "text"

    @classmethod
    def get_fields_recursively(cls, p_key, properties_dict: Dict, field_types=None) -> List:
        """
        递归拿取mapping集合获取所有的index下的fields
        :param p_key:
        :param properties_dict:
        :param field_types:
        :return:
        """
        fields_result: List = list()
        common_index: int = 1
        for key in properties_dict.keys():
            if "properties" in key:
                fields_result.extend(cls.get_fields_recursively(p_key=p_key, properties_dict=properties_dict[key]))
            else:
                if key in ["include_in_all"] or not isinstance(properties_dict[key], dict):
                    continue
                k_keys: List = properties_dict[key].keys()
                filed_name: str = "{}.{}".format(p_key, key)
                if "type" in k_keys:
                    field_type: str = properties_dict[key]["type"]
                    if field_types and field_type not in field_types:
                        continue
                    doc_values_farther_dict: dict = properties_dict[key]
                    doc_values = None
                    if isinstance(doc_values_farther_dict, dict):
                        doc_values = doc_values_farther_dict.get("doc_values", True)

                    es_doc_values = doc_values
                    if field_type in ["text", "object"]:
                        es_doc_values = False

                    # @TODO tag：兼容前端代码，后面需要删除
                    tag = "metric"
                    if field_type == "date":
                        tag = "timestamp"
                    elif es_doc_values:
                        tag = "dimension"

                    data = dict()
                    data.update(
                        {
                            "field_type": field_type,
                            "field_name": filed_name,
                            "es_index": common_index,
                            # "analyzed": analyzed,
                            "field_alias": "",
                            "description": "",
                            "es_doc_values": es_doc_values,
                            "tag": tag,
                            "is_analyzed": cls._is_analyzed(field_type),
                        }
                    )
                    fields_result.append(data)
                elif "properties" in k_keys:
                    fields_result.extend(
                        cls.get_fields_recursively(
                            p_key="{}.{}".format(p_key, key), properties_dict=properties_dict[key]
                        )
                    )
        return fields_result

    @staticmethod
    def compare_indices_by_date(index_a, index_b):
        index_a = list(index_a.keys())[0]
        index_b = list(index_b.keys())[0]

        def convert_to_normal_date_tuple(index_name) -> tuple:
            # example 1: 2_bklog_xxxx_20200321_1 -> (20200321, 1)
            # example 2: 2_xxxx_2020032101 -> (20200321, 1)
            result = re.findall(r"(\d{8})_(\d{1,7})$", index_name) or re.findall(r"(\d{8})(\d{2})$", index_name)
            if result:
                return result[0][0], int(result[0][1])
            # not match
            return index_name, 0

        converted_index_a = convert_to_normal_date_tuple(index_a)
        converted_index_b = convert_to_normal_date_tuple(index_b)

        return (converted_index_a > converted_index_b) - (converted_index_a < converted_index_b)

    def find_megerd_property(self, mapping_result) -> dict:
        return self._merge_property(self._get_all_property(mapping_result))

    def _get_all_property(self, mapping_result):
        index_es_rt: str = self.indices.replace(".", "_")
        index_es_rts = index_es_rt.split(",")
        mapping_group: dict = self._mapping_group(index_es_rts, mapping_result)
        return [self.find_property_dict_first(mapping_list) for mapping_list in mapping_group.values()]

    def _merge_property(self, propertys: list):
        merge_dict = {}
        for property in propertys:
            for property_key, property_define in property.items():
                if property_key not in merge_dict:
                    merge_dict[property_key] = property_define
                    continue
                if merge_dict[property_key]["type"] != property_define["type"]:
                    merge_dict[property_key]["is_conflict"] = True
        return {
            property_key: property for property_key, property in merge_dict.items() if not property.get("is_conflict")
        }

    def _mapping_group(self, index_result_tables: list, mapping_result: list):
        # 第三方不合并mapping
        if self.scenario_id in [Scenario.ES]:
            return {"es": mapping_result}
        mapping_group = defaultdict(list)
        # 排序rt表 最长的在前面保障类似 bk_test_test, bk_test
        index_result_tables.sort(key=lambda s: len(s), reverse=True)
        # 数平rt和索引对应不区分大小写
        if self.scenario_id in [Scenario.BKDATA]:
            index_result_tables = [index.lower() for index in index_result_tables]
        for mapping in mapping_result:
            index: str = next(iter(mapping.keys()))
            for index_es_rt in index_result_tables:
                if index_es_rt in index:
                    mapping_group[index_es_rt].append(mapping)
                    break
        return mapping_group

    @classmethod
    def find_property_dict_first(cls, result_list: list) -> Dict:
        """
        获取最新索引mapping
        :param result_list:
        :return:
        """
        sorted_result_list = sorted(result_list, key=functools.cmp_to_key(cls.compare_indices_by_date), reverse=True)
        property_result_dict: dict = {}
        for _inner_dict in sorted_result_list:
            property_dict = cls.get_property_dict(_inner_dict)
            if property_dict:
                property_result_dict = property_dict
                break
        return property_result_dict

    def _combine_description_field(self, fields_list=None, scope=None):
        if fields_list is None:
            return []
        # mapping 和schema对比
        schema_result: list = []
        if self.scenario_id in [Scenario.BKDATA]:
            schema_result: list = self.get_bkdata_schema(self.indices)
        if self.scenario_id in [Scenario.LOG]:
            schema_result: list = self.get_meta_schema(self.indices)

        # list to dict
        schema_dict: dict = {}
        for item in schema_result:
            _field_name = item.get("field_name", "")
            temp_dict: dict = {}
            for k, v in item.items():
                temp_dict.update({k: v})
            if _field_name:
                schema_dict.update({_field_name: temp_dict})

        # 增加description别名字段
        for _field in fields_list:
            a_field_name = _field.get("field_name", "")
            if a_field_name:
                field_info = schema_dict.get(a_field_name)
                if field_info:
                    if self.scenario_id in [Scenario.BKDATA]:
                        field_alias: str = field_info.get("field_alias")
                    elif self.scenario_id in [Scenario.LOG]:
                        field_alias: str = field_info.get("description")
                    else:
                        field_alias: str = ""
                    _field.update({"description": field_alias, "field_alias": field_alias})
                else:
                    _field.update({"description": None})
        return fields_list

    def get_bkdata_schema(self, index: str) -> list:
        index, *_ = index.split(",")
        return self._inner_get_bkdata_schema(index=index)

    @staticmethod
    @cache_one_hour("{index}_schema")
    def _inner_get_bkdata_schema(*, index):
        try:
            data: dict = BkDataStorekitApi.get_schema_and_sql({"result_table_id": index})
            field_list: list = data["storage"]["es"]["fields"]
            return field_list
        except SearchGetSchemaException:
            return []

    def get_meta_schema(self, index: str) -> list:
        index, *_ = index.split(",")
        return self._inner_get_meta_schema(index=index)

    @staticmethod
    @cache_one_hour("{index}_schema")
    def _inner_get_meta_schema(*, index):
        try:
            data: dict = TransferApi.get_result_table({"table_id": index})
            field_list: list = data["field_list"]
            return field_list
        except Exception:  # pylint: disable=broad-except
            return []

    def _combine_fields(self, fields_list):
        """
        组装fields
        :param fields_list:
        :return:
        """

        # inner
        if self.scenario_id == Scenario.BKDATA:
            return self.combine_bkdata_fields(fields_list)
        # original es
        if self.scenario_id == Scenario.ES:
            return self.combine_es_fields(fields_list, self.time_field)
        return self.combine_bkdata_fields(fields_list)

    @staticmethod
    def combine_bkdata_fields(fields_list):
        """
        for bkdata
        :param fields_list:
        :return:
        """
        final_fields_list = list()
        commit_list = list()
        common_list = list()
        time_list = list()
        produce_list = list()
        for s_field in fields_list:
            field_name = s_field["field_name"]
            field_type = s_field["field_type"]
            if isinstance(field_name, str):
                field_name = field_name.lower()
            if field_name in INNER_PRODUCE_FIELDS:
                s_field["is_editable"] = True
                produce_list.append(s_field)
                continue
            if field_name in INNER_COMMIT_FIELDS:
                commit_list.append(s_field)
            elif field_type in TIME_TYPE:
                time_list.append(s_field)
            else:
                common_list.append(s_field)
        if len(commit_list) <= 1:
            final_fields_list.extend(commit_list)
        else:
            for common_single in commit_list:
                if common_single["field_name"].lower() == "report_time":
                    final_fields_list.append(common_single)
        final_fields_list.extend(time_list)
        final_fields_list.extend(common_list)
        final_fields_list.extend(produce_list)
        return final_fields_list

    @staticmethod
    def combine_es_fields(fields_list, time_field):
        """
        for es
        :param fields_list:
        :return:
        """
        final_fields_list = list()
        commit_list = list()
        common_list = list()
        time_list = list()
        produce_list = list()
        for s_field in fields_list:
            field_name = s_field["field_name"]
            field_type = s_field["field_type"]
            if isinstance(field_name, str):
                field_name = field_name.lower()
            if field_name in OUTER_PRODUCE_FIELDS:
                s_field["is_editable"] = False
                produce_list.append(s_field)
                continue
            if field_name == time_field:
                commit_list.append(s_field)
            elif field_type in TIME_TYPE:
                time_list.append(s_field)
            else:
                common_list.append(s_field)
        final_fields_list.extend(commit_list)
        final_fields_list.extend(time_list)
        final_fields_list.extend(common_list)
        final_fields_list.extend(produce_list)
        return final_fields_list

    @staticmethod
    def _sort_display_fields(display_fields: list) -> list:
        """
        检索字段显示时间排序规则: 默认dtEventTimeStamp放前面，time放最后
        :param display_fields:
        :return:
        """
        if "dtEventTimeStamp" in display_fields:
            dt_time_index = display_fields.index("dtEventTimeStamp")
            if dt_time_index != 0:
                display_fields[0], display_fields[dt_time_index] = "dtEventTimeStamp", display_fields[0]

        if "time" in display_fields:
            time_index = display_fields.index("time")
            if time_index != len(display_fields) - 1:
                display_fields[-1], display_fields[time_index] = "time", display_fields[-1]
        return display_fields

    @classmethod
    def get_sort_list_by_index_id(cls, index_set_id, scope="default"):
        username = get_request_username()
        index_config_obj = UserIndexSetConfig.objects.filter(
            index_set_id=index_set_id, created_by=username, scope=scope, is_deleted=False
        )
        if not index_config_obj.exists():
            return list()

        sort_list = index_config_obj.first().sort_list
        return sort_list if isinstance(sort_list, list) else list()

    @classmethod
    def init_ip_topo_switch(cls, index_set_id: int) -> bool:
        log_index_set_obj = LogIndexSet.objects.filter(index_set_id=index_set_id).first()
        project_id = log_index_set_obj.project_id
        if not project_id:
            return False
        project_obj = ProjectInfo.objects.filter(project_id=project_id).first()
        if not project_obj:
            return False
        # 如果第三方es的话设置为ip_topo_switch为False
        if log_index_set_obj.scenario_id == Scenario.ES:
            return False
        return project_obj.ip_topo_switch

    @classmethod
    def analyze_fields(cls, final_fields_list: List[Dict[str, Any]]) -> dict:
        # 上下文实时日志可否使用判断
        fields_list = [x["field_name"] for x in final_fields_list]
        context_search_usable: bool = False
        realtime_search_usable: bool = False
        fields_list = set(fields_list)

        context_and_realtime_judge_fields = [
            {"gseindex", "ip", "path", "_iteration_idx"},
            {"gseindex", "container_id", "logfile", "_iteration_idx"},
            {"gseIndex", "serverIp", "path", "_iteration_idx"},
            {"gseIndex", "serverIp", "path", "iterationIndex"},
        ]
        if any(fields_list.issuperset(judge) for judge in context_and_realtime_judge_fields):
            context_search_usable = True
            realtime_search_usable = True
            return {
                "context_search_usable": context_search_usable,
                "realtime_search_usable": realtime_search_usable,
                "usable_reason": "",
            }
        return {
            "context_search_usable": context_search_usable,
            "realtime_search_usable": realtime_search_usable,
            "usable_reason": cls._analyze_require_fields(fields_list),
        }

    @classmethod
    def _analyze_require_fields(cls, fields_list):
        def _analyze_path_fields(fields):
            if "path" and "logfile" not in fields:
                return _("必须path或者logfile字段")
            return ""

        if "gseindex" in fields_list:
            if "_iteration_idx" not in fields_list:
                return _("必须_iteration_idx字段")

            if "ip" in fields_list:
                return _analyze_path_fields(fields_list)
            if "container_id" in fields_list:
                return _analyze_path_fields(fields_list)
            return _("必须ip或者container_id字段")

        elif "gseIndex" in fields_list:

            if "serverIp" not in fields_list:
                return _("必须serverIp字段")

            if "path" not in fields_list:
                return _("必须path字段")

            if "iterationIndex" and "_iteration_idx" not in fields_list:
                return _("必须iterationIndex或者_iteration_idx字段")
            return ""
        return _("必须gseindex或者gseIndex字段")

    @classmethod
    def get_date_candidate(cls, mapping_list: list):
        """
        1、校验索引mapping字段类型是否一致；
        2、获取可供选择的时间字段（long&data类型）
        """
        date_field_list: list = []
        for item in mapping_list:
            property_dict = cls.get_property_dict(item)
            if property_dict:
                item_data_field = []
                for key, info in property_dict.items():
                    field_type = info.get("type", "")
                    if field_type in settings.FEATURE_TOGGLE.get("es_date_candidate", ["date", "long"]):
                        item_data_field.append("{}:{}".format(key, field_type))
                # 校验是否有相同的时间字段（long和date类型)
                if not date_field_list:
                    date_field_list = item_data_field
                date_field_list = list(set(date_field_list).intersection(item_data_field))
                if not date_field_list:
                    raise FieldsDateNotExistException()
        if not date_field_list:
            raise FieldsDateNotExistException()

        date_candidate = []
        for _field in date_field_list:
            field_name, field_type = _field.split(":")
            date_candidate.append({"field_name": field_name, "field_type": field_type})
        return date_candidate

    @classmethod
    def get_property_dict(cls, dict_item, match_key="properties"):
        """
        根据ES-mapping获取首个properties的字段列表
        """
        if match_key in dict_item:
            return dict_item[match_key]
        for _key, _value in dict_item.items():
            if isinstance(_value, dict):
                result = cls.get_property_dict(_value, match_key)
                if result:
                    return result
        return None

    @classmethod
    def async_export_fields(cls, final_fields_list: List[Dict[str, Any]], scenario_id: str) -> dict:
        """
        判断是否可以支持大额导出
        """
        fields = {final_field["field_name"] for final_field in final_fields_list if final_field["es_doc_values"]}
        result = {"async_export_usable": False, "async_export_fields": [], "async_export_usable_reason": ""}
        if not FeatureToggleObject.switch(FEATURE_ASYNC_EXPORT_COMMON):
            result["async_export_usable_reason"] = _("【异步导出功能尚未开放】")
            return result

        if scenario_id == Scenario.BKDATA and fields.issuperset(set(BKDATA_ASYNC_FIELDS)):
            result["async_export_usable"] = True
            result["async_export_fields"] = BKDATA_ASYNC_FIELDS
            return result

        if scenario_id == Scenario.BKDATA and fields.issuperset(set(BKDATA_ASYNC_CONTAINER_FIELDS)):
            result["async_export_usable"] = True
            result["async_export_fields"] = BKDATA_ASYNC_CONTAINER_FIELDS
            return result

        if scenario_id == Scenario.LOG and fields.issuperset(set(LOG_ASYNC_FIELDS)):
            result["async_export_usable"] = True
            result["async_export_fields"] = LOG_ASYNC_FIELDS
            return result

        if scenario_id == Scenario.ES:
            result["async_export_usable"] = True
            return result

        return cls._generate_async_export_reason(scenario_id=scenario_id, result=result)

    @classmethod
    def _generate_async_export_reason(cls, scenario_id: str, result: dict):
        reason_map = {
            Scenario.BKDATA: _("【异步导出缺少必备字段: {async_fields} or {async_container_fields}】").format(
                async_fields=BKDATA_ASYNC_FIELDS, async_container_fields=BKDATA_ASYNC_CONTAINER_FIELDS
            ),
            Scenario.LOG: _("【异步导出缺少必备字段: {async_fields}】").format(async_fields=LOG_ASYNC_FIELDS),
        }

        result["async_export_usable_reason"] = reason_map[scenario_id]
        return result
