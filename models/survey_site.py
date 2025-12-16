"""
調査地モデル
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class SurveySite:
    """調査地モデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, parent_site_id: int, name: str, latitude: float, longitude: float,
               altitude: Optional[float] = None, area: Optional[float] = None,
               remarks: Optional[str] = None) -> Optional[int]:
        """新規調査地を作成"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO survey_sites 
                (parent_site_id, name, latitude, longitude, altitude, area, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (parent_site_id, name, latitude, longitude, altitude, area, remarks))
            
            self.conn.commit()
            site_id = cursor.lastrowid
            
            logger.info(f"Survey site created: {name} (ID: {site_id})")
            return site_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                logger.error(f"Survey site name already exists in this parent site: {name}")
            elif "FOREIGN KEY constraint" in str(e):
                logger.error(f"Parent site not found: {parent_site_id}")
            else:
                logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create survey site: {e}")
            return None
    
    def get_by_id(self, site_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """IDで調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ss.*, ps.name as parent_site_name
                FROM survey_sites ss
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                WHERE ss.id = ?
            """
            
            if not include_deleted:
                query += " AND ss.deleted_at IS NULL"
            
            cursor.execute(query, (site_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get survey site by ID: {e}")
            return None
    
    def get_by_parent(self, parent_site_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """親調査地IDで調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ss.*, ps.name as parent_site_name
                FROM survey_sites ss
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                WHERE ss.parent_site_id = ?
            """
            
            if not include_deleted:
                query += " AND ss.deleted_at IS NULL"
            
            query += " ORDER BY ss.name"
            
            cursor.execute(query, (parent_site_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get survey sites by parent: {e}")
            return []
    
    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """全ての調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT ss.*, ps.name as parent_site_name
                FROM survey_sites ss
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
            """
            
            if not include_deleted:
                query += " WHERE ss.deleted_at IS NULL"
            
            query += " ORDER BY ps.name, ss.name"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all survey sites: {e}")
            return []
    
    def update(self, site_id: int, **kwargs) -> bool:
        """調査地を更新"""
        try:
            allowed_fields = ['parent_site_id', 'name', 'latitude', 'longitude', 
                            'altitude', 'area', 'remarks']
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [site_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE survey_sites 
                SET {set_clause}
                WHERE id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey site not found or already deleted: {site_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey site updated: ID {site_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Update failed due to integrity constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update survey site: {e}")
            return False
    
    def delete(self, site_id: int, logical: bool = True) -> bool:
        """調査地を削除"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                cursor.execute("""
                    UPDATE survey_sites 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND deleted_at IS NULL
                """, (site_id,))
            else:
                cursor.execute("DELETE FROM survey_sites WHERE id = ?", (site_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey site not found or already deleted: {site_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey site deleted: ID {site_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete survey site: {e}")
            return False
    
    def restore(self, site_id: int) -> bool:
        """論理削除された調査地を復元"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE survey_sites 
                SET deleted_at = NULL 
                WHERE id = ? AND deleted_at IS NOT NULL
            """, (site_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey site not found or not deleted: {site_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey site restored: ID {site_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to restore survey site: {e}")
            return False