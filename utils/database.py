"""Database management and persistence"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import json

from utils.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class Review(Base):
    """Review data model"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(100), nullable=False, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    date = Column(String(50))
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON)


class AnalysisResult(Base):
    """Analysis result data model"""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), index=True)
    patterns = Column(JSON)
    ai_analysis = Column(JSON)
    product_ideas = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)


class DatabaseManager:
    """Database connection and operation manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database URL (defaults to SQLite)
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", "sqlite:///./data/app.db"
        )
        
        # Create data directory for SQLite
        if self.database_url.startswith("sqlite"):
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use StaticPool for SQLite to handle concurrent access
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(self.database_url)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info("Database initialized", database_url=self.database_url)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def save_reviews(self, tool_name: str, reviews: List[Dict[str, Any]]) -> int:
        """
        Save reviews to database
        
        Args:
            tool_name: Name of the tool
            reviews: List of review dictionaries
            
        Returns:
            Number of reviews saved
        """
        session = self.get_session()
        try:
            count = 0
            for review_data in reviews:
                review = Review(
                    tool_name=tool_name,
                    text=review_data.get("text", ""),
                    rating=review_data.get("rating", 0),
                    date=review_data.get("date"),
                    source=review_data.get("source", "unknown"),
                    metadata=review_data.get("metadata")
                )
                session.add(review)
                count += 1
            
            session.commit()
            logger.info("Reviews saved", tool_name=tool_name, count=count)
            return count
        except Exception as e:
            session.rollback()
            logger.error("Error saving reviews", error=str(e))
            raise
        finally:
            session.close()
    
    def get_reviews(self, tool_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve reviews from database
        
        Args:
            tool_name: Filter by tool name (optional)
            limit: Maximum number of reviews to return
            
        Returns:
            List of review dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(Review)
            if tool_name:
                query = query.filter(Review.tool_name == tool_name)
            
            reviews = query.order_by(Review.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "text": r.text,
                    "rating": r.rating,
                    "date": r.date,
                    "source": r.source,
                    "metadata": r.metadata
                }
                for r in reviews
            ]
        finally:
            session.close()
    
    def save_analysis_result(
        self,
        tool_name: str,
        session_id: str,
        patterns: Dict[str, Any],
        ai_analysis: Dict[str, Any],
        product_ideas: List[Dict[str, Any]],
        retention_days: int = 90
    ) -> int:
        """
        Save analysis result
        
        Args:
            tool_name: Name of the tool
            session_id: Session identifier
            patterns: Pattern extraction results
            ai_analysis: AI analysis results
            product_ideas: Product ideas
            retention_days: Days to retain data
            
        Returns:
            ID of saved result
        """
        session = self.get_session()
        try:
            expires_at = datetime.utcnow() + timedelta(days=retention_days)
            
            result = AnalysisResult(
                tool_name=tool_name,
                session_id=session_id,
                patterns=patterns,
                ai_analysis=ai_analysis,
                product_ideas=product_ideas,
                expires_at=expires_at
            )
            
            session.add(result)
            session.commit()
            
            logger.info("Analysis result saved", tool_name=tool_name, result_id=result.id)
            return result.id
        except Exception as e:
            session.rollback()
            logger.error("Error saving analysis result", error=str(e))
            raise
        finally:
            session.close()
    
    def get_analysis_result(self, result_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve analysis result by ID
        
        Args:
            result_id: Result ID
            
        Returns:
            Analysis result dictionary or None
        """
        session = self.get_session()
        try:
            result = session.query(AnalysisResult).filter(
                AnalysisResult.id == result_id
            ).first()
            
            if not result:
                return None
            
            return {
                "id": result.id,
                "tool_name": result.tool_name,
                "session_id": result.session_id,
                "patterns": result.patterns,
                "ai_analysis": result.ai_analysis,
                "product_ideas": result.product_ideas,
                "created_at": result.created_at.isoformat(),
                "expires_at": result.expires_at.isoformat() if result.expires_at else None
            }
        finally:
            session.close()
    
    def cleanup_expired_data(self) -> int:
        """
        Clean up expired analysis results (GDPR compliance)
        
        Returns:
            Number of records deleted
        """
        session = self.get_session()
        try:
            now = datetime.utcnow()
            deleted = session.query(AnalysisResult).filter(
                AnalysisResult.expires_at < now
            ).delete()
            
            session.commit()
            logger.info("Expired data cleaned up", deleted_count=deleted)
            return deleted
        except Exception as e:
            session.rollback()
            logger.error("Error cleaning up expired data", error=str(e))
            return 0
        finally:
            session.close()
    
    def delete_user_data(self, session_id: str) -> int:
        """
        Delete all data for a session (GDPR right to deletion)
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of records deleted
        """
        session = self.get_session()
        try:
            # Delete analysis results
            deleted_results = session.query(AnalysisResult).filter(
                AnalysisResult.session_id == session_id
            ).delete()
            
            session.commit()
            logger.info("User data deleted", session_id=session_id, deleted_count=deleted_results)
            return deleted_results
        except Exception as e:
            session.rollback()
            logger.error("Error deleting user data", error=str(e))
            return 0
        finally:
            session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
