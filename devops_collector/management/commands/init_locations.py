import logging
from sqlalchemy.orm import Session

from devops_collector.core.management import BaseCommand
from devops_collector.models.base_models import Location


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "初始化地理位置主数据 (mdm_locations)"

    def handle(self, session: Session):
        # 定义预置数据
        locations_data = [
            # --- 特殊位置 ---
            {
                "location_code": "LOC-NATIONWIDE",
                "code": "nationwide",
                "location_name": "全国",
                "short_name": "全国",
                "location_type": "region",
                "region": "全国",
                "parent_code": None,
            },
            # --- 直辖市 ---
            {"code": "beijing", "name": "北京市", "short": "北京", "region": "华北"},
            {"code": "shanghai", "name": "上海市", "short": "上海", "region": "华东"},
            {"code": "tianjin", "name": "天津市", "short": "天津", "region": "华北"},
            {"code": "chongqing", "name": "重庆市", "short": "重庆", "region": "西南"},
            # --- 省份 ---
            {"code": "anhui", "name": "安徽省", "short": "安徽", "region": "华东"},
            {"code": "fujian", "name": "福建省", "short": "福建", "region": "华东"},
            {"code": "gansu", "name": "甘肃省", "short": "甘肃", "region": "西北"},
            {"code": "guangdong", "name": "广东省", "short": "广东", "region": "华南"},
            {"code": "guizhou", "name": "贵州省", "short": "贵州", "region": "西南"},
            {"code": "hainan", "name": "海南省", "short": "海南", "region": "华南"},
            {"code": "hebei", "name": "河北省", "short": "河北", "region": "华北"},
            {"code": "henan", "name": "河南省", "short": "河南", "region": "华中"},
            {"code": "heilongjiang", "name": "黑龙江省", "short": "黑龙江", "region": "东北"},
            {"code": "hubei", "name": "湖北省", "short": "湖北", "region": "华中"},
            {"code": "hunan", "name": "湖南省", "short": "湖南", "region": "华中"},
            {"code": "jilin", "name": "吉林省", "short": "吉林", "region": "东北"},
            {"code": "jiangsu", "name": "江苏省", "short": "江苏", "region": "华东"},
            {"code": "jiangxi", "name": "江西省", "short": "江西", "region": "华东"},
            {"code": "liaoning", "name": "辽宁省", "short": "辽宁", "region": "东北"},
            {"code": "qinghai", "name": "青海省", "short": "青海", "region": "西北"},
            {"code": "shaanxi", "name": "陕西省", "short": "陕西", "region": "西北"},
            {"code": "shandong", "name": "山东省", "short": "山东", "region": "华东"},
            {"code": "shanxi", "name": "山西省", "short": "山西", "region": "华北"},
            {"code": "sichuan", "name": "四川省", "short": "四川", "region": "西南"},
            {"code": "yunnan", "name": "云南省", "short": "云南", "region": "西南"},
            {"code": "zhejiang", "name": "浙江省", "short": "浙江", "region": "华东"},
            # --- 自治区 ---
            {"code": "guangxi", "name": "广西壮族自治区", "short": "广西", "region": "华南"},
            {"code": "neimenggu", "name": "内蒙古自治区", "short": "内蒙古", "region": "华北"},
            {"code": "ningxia", "name": "宁夏回族自治区", "short": "宁夏", "region": "西北"},
            {"code": "xinjiang", "name": "新疆维吾尔自治区", "short": "新疆", "region": "西北"},
            {"code": "xizang", "name": "西藏自治区", "short": "西藏", "region": "西南"},
            # --- 特别行政区 ---
            {"code": "hongkong", "name": "香港特别行政区", "short": "香港", "region": "华南"},
            {"code": "macau", "name": "澳门特别行政区", "short": "澳门", "region": "华南"},
            {"code": "taiwan", "name": "台湾省", "short": "台湾", "region": "华东"},
        ]

        try:
            # 第一遍：创建/更新所有位置（不含 parent_id）
            code_to_id = {}
            for item in locations_data:
                match_code = item["code"]
                if "location_code" in item:
                    data_dict = {
                        "location_code": item["location_code"],
                        "code": item["code"],
                        "location_name": item["location_name"],
                        "short_name": item["short_name"],
                        "location_type": item["location_type"],
                        "region": item["region"],
                    }
                else:
                    data_dict = {
                        "location_code": f"LOC-{match_code.upper()}",
                        "code": match_code,
                        "location_name": item["name"],
                        "short_name": item["short"],
                        "location_type": "province",
                        "region": item["region"],
                    }

                exists = self.session.query(Location).filter_by(code=match_code).first()
                if exists:
                    for k, v in data_dict.items():
                        setattr(exists, k, v)
                    self.session.flush()
                    code_to_id[data_dict["location_code"]] = exists.id
                else:
                    new_loc = Location(**data_dict)
                    self.session.add(new_loc)
                    self.session.flush()
                    code_to_id[data_dict["location_code"]] = new_loc.id

            # 第二遍：设置 parent_id
            nationwide_id = code_to_id.get("LOC-NATIONWIDE")
            if nationwide_id:
                all_locs = self.session.query(Location).all()
                for loc in all_locs:
                    if loc.location_code != "LOC-NATIONWIDE":
                        loc.parent_id = nationwide_id

            self.session.flush()
            self.stdout.write("✅ 位置主数据初始化完成。\n")
            return True

        except Exception as e:
            logger.error(f"位置初始化失败: {e}")
            return False
