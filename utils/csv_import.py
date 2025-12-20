"""
CSVインポートユーティリティ
"""
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CSVImporter:
    """CSVインポートクラス"""
    
    def __init__(self, database):
        self.database = database
        self.conn = database.connect()
        self.errors = []
    
    def import_parent_sites(self, file_path: str) -> Tuple[int, List[str]]:
        """
        親調査地をインポート
        
        Returns:
        --------
        Tuple[int, List[str]]
            (成功件数, エラーリスト)
        """
        try:
            from models.parent_site import ParentSite
            
            # CSV読み込み
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # 必須カラムチェック
            required_cols = ['名称', '緯度', '経度']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return 0, [f"必須カラムがありません: {', '.join(missing_cols)}"]
            
            model = ParentSite(self.conn)
            success_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    # バリデーション
                    name = str(row['名称']).strip()
                    if not name or name == 'nan':
                        errors.append(f"行{idx+2}: 名称が空です")
                        continue
                    
                    try:
                        latitude = float(row['緯度'])
                        longitude = float(row['経度'])
                    except (ValueError, TypeError):
                        errors.append(f"行{idx+2}: 緯度経度が数値ではありません")
                        continue
                    
                    if not (20 <= latitude <= 46):
                        errors.append(f"行{idx+2}: 緯度が範囲外です ({latitude})")
                        continue
                    
                    if not (122 <= longitude <= 154):
                        errors.append(f"行{idx+2}: 経度が範囲外です ({longitude})")
                        continue
                    
                    # オプション項目
                    altitude = None
                    if '標高' in df.columns and pd.notna(row['標高']):
                        try:
                            altitude = float(row['標高'])
                        except ValueError:
                            pass
                    
                    area = None
                    if '面積' in df.columns and pd.notna(row['面積']):
                        try:
                            area = float(row['面積'])
                        except ValueError:
                            pass
                    
                    remarks = None
                    if '備考' in df.columns and pd.notna(row['備考']):
                        remarks = str(row['備考'])
                    
                    # 登録
                    site_id = model.create(
                        name=name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=altitude,
                        area=area,
                        remarks=remarks
                    )
                    
                    if site_id:
                        success_count += 1
                    else:
                        errors.append(f"行{idx+2}: 登録失敗 (名称重複の可能性: {name})")
                
                except Exception as e:
                    errors.append(f"行{idx+2}: {str(e)}")
            
            logger.info(f"Parent sites imported: {success_count}/{len(df)}")
            return success_count, errors
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return 0, [f"ファイル読み込みエラー: {str(e)}"]
    
    def import_survey_sites(self, file_path: str) -> Tuple[int, List[str]]:
        """調査地をインポート"""
        try:
            from models.survey_site import SurveySite
            from models.parent_site import ParentSite
            
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            required_cols = ['親調査地名', '名称', '緯度', '経度']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return 0, [f"必須カラムがありません: {', '.join(missing_cols)}"]
            
            parent_model = ParentSite(self.conn)
            survey_model = SurveySite(self.conn)
            
            # 親調査地名→IDマッピング
            parent_sites = parent_model.get_all()
            parent_name_to_id = {ps['name']: ps['id'] for ps in parent_sites}
            
            success_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    parent_name = str(row['親調査地名']).strip()
                    if parent_name not in parent_name_to_id:
                        errors.append(f"行{idx+2}: 親調査地「{parent_name}」が存在しません")
                        continue
                    
                    parent_site_id = parent_name_to_id[parent_name]
                    
                    name = str(row['名称']).strip()
                    if not name or name == 'nan':
                        errors.append(f"行{idx+2}: 名称が空です")
                        continue
                    
                    latitude = float(row['緯度'])
                    longitude = float(row['経度'])
                    
                    if not (20 <= latitude <= 46):
                        errors.append(f"行{idx+2}: 緯度が範囲外です")
                        continue
                    
                    if not (122 <= longitude <= 154):
                        errors.append(f"行{idx+2}: 経度が範囲外です")
                        continue
                    
                    altitude = None
                    if '標高' in df.columns and pd.notna(row['標高']):
                        altitude = float(row['標高'])
                    
                    area = None
                    if '面積' in df.columns and pd.notna(row['面積']):
                        area = float(row['面積'])
                    
                    remarks = None
                    if '備考' in df.columns and pd.notna(row['備考']):
                        remarks = str(row['備考'])
                    
                    site_id = survey_model.create(
                        parent_site_id=parent_site_id,
                        name=name,
                        latitude=latitude,
                        longitude=longitude,
                        altitude=altitude,
                        area=area,
                        remarks=remarks
                    )
                    
                    if site_id:
                        success_count += 1
                    else:
                        errors.append(f"行{idx+2}: 登録失敗 ({name})")
                
                except Exception as e:
                    errors.append(f"行{idx+2}: {str(e)}")
            
            logger.info(f"Survey sites imported: {success_count}/{len(df)}")
            return success_count, errors
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return 0, [f"ファイル読み込みエラー: {str(e)}"]
    
    def import_species(self, file_path: str) -> Tuple[int, List[str]]:
        """種名マスタをインポート"""
        try:
            from models.species import Species
            
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            required_cols = ['学名']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return 0, [f"必須カラムがありません: {', '.join(missing_cols)}"]
            
            model = Species(self.conn)
            success_count = 0
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    scientific_name = str(row['学名']).strip()
                    if not scientific_name or scientific_name == 'nan':
                        errors.append(f"行{idx+2}: 学名が空です")
                        continue
                    
                    genus = str(row.get('属', '')).strip() or None
                    subfamily = str(row.get('亜科', '')).strip() or None
                    ja_name = str(row.get('和名', '')).strip() or None
                    ja_genus = str(row.get('和名属', '')).strip() or None
                    ja_subfamily = str(row.get('和名亜科', '')).strip() or None
                    remarks = str(row.get('備考', '')).strip() or None
                    
                    species_id = model.create(
                        scientific_name=scientific_name,
                        genus=genus,
                        subfamily=subfamily,
                        ja_name=ja_name,
                        ja_genus=ja_genus,
                        ja_subfamily=ja_subfamily,
                        remarks=remarks
                    )
                    
                    if species_id:
                        success_count += 1
                    else:
                        errors.append(f"行{idx+2}: 登録失敗 (学名重複または形式エラー: {scientific_name})")
                
                except Exception as e:
                    errors.append(f"行{idx+2}: {str(e)}")
            
            logger.info(f"Species imported: {success_count}/{len(df)}")
            return success_count, errors
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return 0, [f"ファイル読み込みエラー: {str(e)}"]
    
    def generate_template(self, template_type: str, output_path: str) -> bool:
        """テンプレートCSVを生成"""
        try:
            if template_type == "parent_sites":
                df = pd.DataFrame(columns=['名称', '緯度', '経度', '標高', '面積', '備考'])
                df.loc[0] = ['中部_南信', 35.857, 137.934, 650, 500000, '長野県上伊那郡']
            
            elif template_type == "survey_sites":
                df = pd.DataFrame(columns=['親調査地名', '名称', '緯度', '経度', '標高', '面積', '備考'])
                df.loc[0] = ['中部_南信', '上伊那_信州大学', 35.865, 137.937, 767.1, 480000, 'キャンパス']
            
            elif template_type == "species":
                df = pd.DataFrame(columns=['学名', '属', '亜科', '和名', '和名属', '和名亜科', '備考'])
                df.loc[0] = ['Camponotus japonicus', 'Camponotus', 'Formicinae', 'クロオオアリ', 'オオアリ', 'ヤマアリ', '']
            
            else:
                return False
            
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"Template generated: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Template generation failed: {e}")
            return False