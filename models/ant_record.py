"""
アリ類出現記録モデル
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class AntRecord:
    """アリ類出現記録モデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, survey_event_id: int, species_id: int, count: int,
               remarks: Optional[str] = None) -> Optional[int]:
        """新規アリ類記録を作成"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO ant_records (survey_event_id, species_id, count, remarks)
                VALUES (?, ?, ?, ?)
            """, (survey_event_id, species_id, count, remarks))
            
            self.conn.commit()
            record_id = cursor.lastrowid
            
            logger.info(f"Ant record created: Event={survey_event_id}, Species={species_id}, Count={count} (ID: {record_id})")
            return record_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                logger.error(f"Ant record already exists: Event={survey_event_id}, Species={species_id}")
            else:
                logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create ant record: {e}")
            return None
    
    def get_by_id(self, record_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """IDでアリ類記録を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ar.*, sm.scientific_name, sm.ja_name
                FROM ant_records ar
                LEFT JOIN species_master sm ON ar.species_id = sm.id
                WHERE ar.id = ?
            """
            
            if not include_deleted:
                query += " AND ar.deleted_at IS NULL"
            
            cursor.execute(query, (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get ant record by ID: {e}")
            return None
    
    def get_by_event(self, survey_event_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """調査イベントIDでアリ類記録を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ar.*, sm.scientific_name, sm.ja_name, sm.genus, sm.subfamily
                FROM ant_records ar
                LEFT JOIN species_master sm ON ar.species_id = sm.id
                WHERE ar.survey_event_id = ?
            """
            
            if not include_deleted:
                query += " AND ar.deleted_at IS NULL"
            
            query += " ORDER BY sm.scientific_name"
            
            cursor.execute(query, (survey_event_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get ant records by event: {e}")
            return []
    
    def get_by_species(self, species_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """種IDでアリ類記録を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ar.*, se.survey_date, se.survey_site, 
                       ss.name as survey_site_name, ps.name as parent_site_name
                FROM ant_records ar
                LEFT JOIN survey_events se ON ar.survey_event_id = se.id
                LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                WHERE ar.species_id = ?
            """
            
            if not include_deleted:
                query += " AND ar.deleted_at IS NULL"
            
            query += " ORDER BY se.survey_date DESC"
            
            cursor.execute(query, (species_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get ant records by species: {e}")
            return []
    
    def update(self, record_id: int, **kwargs) -> bool:
        """アリ類記録を更新"""
        try:
            allowed_fields = ['species_id', 'count', 'remarks']
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [record_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE ant_records 
                SET {set_clause}
                WHERE id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Ant record not found or already deleted: {record_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Ant record updated: ID {record_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Update failed due to integrity constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update ant record: {e}")
            return False
    
    def delete(self, record_id: int, logical: bool = True) -> bool:
        """アリ類記録を削除"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                cursor.execute("""
                    UPDATE ant_records 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND deleted_at IS NULL
                """, (record_id,))
            else:
                cursor.execute("DELETE FROM ant_records WHERE id = ?", (record_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Ant record not found or already deleted: {record_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Ant record deleted: ID {record_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete ant record: {e}")
            return False
    
    def restore(self, record_id: int) -> bool:
        """論理削除されたアリ類記録を復元"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE ant_records 
                SET deleted_at = NULL 
                WHERE id = ? AND deleted_at IS NOT NULL
            """, (record_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Ant record not found or not deleted: {record_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Ant record restored: ID {record_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to restore ant record: {e}")
            return False
    
    def get_statistics_by_species(self, species_id: int) -> Dict[str, Any]:
        """種ごとの統計情報を取得"""
        try:
            cursor = self.conn.cursor()
            
            # 出現頻度（全イベント中での出現率）
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT ar.survey_event_id) as occurrence_count,
                    (SELECT COUNT(*) FROM survey_events WHERE deleted_at IS NULL) as total_events
                FROM ant_records ar
                WHERE ar.species_id = ? AND ar.deleted_at IS NULL
            """, (species_id,))
            
            row = cursor.fetchone()
            occurrence_count = row[0] if row else 0
            total_events = row[1] if row else 1
            occurrence_rate = (occurrence_count / total_events * 100) if total_events > 0 else 0
            
            # 平均・最大・最小個体数
            cursor.execute("""
                SELECT 
                    AVG(count) as avg_count,
                    MAX(count) as max_count,
                    MIN(count) as min_count
                FROM ant_records
                WHERE species_id = ? AND deleted_at IS NULL
            """, (species_id,))
            
            row = cursor.fetchone()
            
            return {
                'occurrence_count': occurrence_count,
                'occurrence_rate': round(occurrence_rate, 2),
                'avg_count': round(row[0], 2) if row and row[0] else 0,
                'max_count': row[1] if row and row[1] else 0,
                'min_count': row[2] if row and row[2] else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get species statistics: {e}")
            return {}