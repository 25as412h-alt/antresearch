"""
植生データモデル
"""
import sqlite3
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class VegetationData:
    """植生データモデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, survey_event_id: int, **kwargs) -> Optional[int]:
        """新規植生データを作成"""
        try:
            # フィールド定義
            fields = [
                'dominant_tree', 'dominant_pretree', 'dominant_sasa', 'dominant_herb', 'litter_type',
                'avg_tree_height', 'avg_pretree_height', 'avg_sasa_height', 'avg_herb_height',
                'avg_litter_height', 'avg_litterL_height', 'avg_litterF_height', 'avg_litterH_height',
                'canopy_coverage', 'precanopy_coverage', 'sasa_coverage', 'herb_coverage',
                'litter_coverage', 'vegetation_rate', 'light_condition', 'soil_moisture'
            ]
            
            # データを抽出
            data = {k: kwargs.get(k) for k in fields}
            data['survey_event_id'] = survey_event_id
            
            cursor = self.conn.cursor()
            
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            
            cursor.execute(f"""
                INSERT INTO vegetation_data ({columns})
                VALUES ({placeholders})
            """, list(data.values()))
            
            self.conn.commit()
            veg_id = cursor.lastrowid
            
            logger.info(f"Vegetation data created: Event={survey_event_id} (ID: {veg_id})")
            return veg_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create vegetation data: {e}")
            return None
    
    def get_by_event(self, survey_event_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """調査イベントIDで植生データを取得"""
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT * FROM vegetation_data WHERE survey_event_id = ?"
            
            if not include_deleted:
                query += " AND deleted_at IS NULL"
            
            cursor.execute(query, (survey_event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get vegetation data by event: {e}")
            return None
    
    def update(self, survey_event_id: int, **kwargs) -> bool:
        """植生データを更新"""
        try:
            allowed_fields = [
                'dominant_tree', 'dominant_pretree', 'dominant_sasa', 'dominant_herb', 'litter_type',
                'avg_tree_height', 'avg_pretree_height', 'avg_sasa_height', 'avg_herb_height',
                'avg_litter_height', 'avg_litterL_height', 'avg_litterF_height', 'avg_litterH_height',
                'canopy_coverage', 'precanopy_coverage', 'sasa_coverage', 'herb_coverage',
                'litter_coverage', 'vegetation_rate', 'light_condition', 'soil_moisture'
            ]
            
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [survey_event_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE vegetation_data 
                SET {set_clause}
                WHERE survey_event_id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Vegetation data not found or already deleted: Event={survey_event_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Vegetation data updated: Event={survey_event_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update vegetation data: {e}")
            return False
    
    def delete(self, survey_event_id: int, logical: bool = True) -> bool:
        """植生データを削除"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                cursor.execute("""
                    UPDATE vegetation_data 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE survey_event_id = ? AND deleted_at IS NULL
                """, (survey_event_id,))
            else:
                cursor.execute("DELETE FROM vegetation_data WHERE survey_event_id = ?", (survey_event_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Vegetation data not found or already deleted: Event={survey_event_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Vegetation data deleted: Event={survey_event_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete vegetation data: {e}")
            return False