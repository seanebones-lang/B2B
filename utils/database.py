"""Database utilities for storing reviews and analysis history"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from utils.logging import get_logger
import os

logger = get_logger(__name__)

Base = declarative_base()


class Review(Base):
    """Review/complaint database model"""
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    tool_name = Column(String(100), nullable=False, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False)
    source = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=True, index=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tool_date', 'tool_name', 'date'),
    )


class AnalysisResult(Base):
    """Analysis result database model"""
    __tablename__ = 'analysis_results'
    
    id = Column(Integer, primary_key=True)
    tool_name = Column(String(100), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False)  # 'pattern', 'idea', 'roadmap'
    result_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_tool_type_date', 'tool_name', 'analysis_type', 'created_at'),
    )


class DatabaseManager:
    """Database manager for reviews and analysis results"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: Database URL (defaults to SQLite if not provided)
        """
        if database_url is None:
            # Default to SQLite for development
            db_path = os.getenv("DATABASE_PATH", "b2b_analyzer.db")
            database_url = f"sqlite:///{db_path}"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info("Database manager initialized", database_url=database_url)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def save_reviews(self, reviews: List[Dict[str, Any]], tool_name: str) -> int:
        """
        Save reviews to database
        
        Args:
            reviews: List of review dictionaries
            tool_name: Name of the tool
            
        Returns:
            Number of reviews saved
        """
        session = self.get_session()
        saved_count = 0
        
        try:
            for review_data in reviews:
                # Parse date if string
                date = review_data.get('date')
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    except:
                        date = None
                
                review = Review(
                    tool_name=tool_name,
                    text=review_data.get('text', ''),
                    rating=review_data.get('rating', 1),
                    source=review_data.get('source', 'unknown'),
                    date=date,
                    metadata=review_data.get('metadata')
                )
                session.add(review)
                saved_count += 1
            
            session.commit()
            logger.info("Reviews saved to database", tool_name=tool_name, count=saved_count)
            
        except Exception as e:
            session.rollback()
            logger.error("Error saving reviews", error=str(e))
            raise
        finally:
            session.close()
        
        return saved_count
    
    def get_reviews(
        self,
        tool_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get reviews from database
        
        Args:
            tool_name: Filter by tool name
            date_from: Filter from date
            date_to: Filter to date
            limit: Maximum number of reviews
            
        Returns:
            List of review dictionaries
        """
        session = self.get_session()
        
        try:
            query = session.query(Review)
            
            if tool_name:
                query = query.filter(Review.tool_name == tool_name)
            
            if date_from:
                query = query.filter(Review.date >= date_from)
            
            if date_to:
                query = query.filter(Review.date <= date_to)
            
            query = query.order_by(Review.date.desc()).limit(limit)
            
            reviews = []
            for review in query.all():
                reviews.append({
                    'text': review.text,
                    'rating': review.rating,
                    'source': review.source,
                    'date': review.date.isoformat() if review.date else None,
                    'metadata': review.metadata,
                    'tool': review.tool_name
                })
            
            return reviews
            
        finally:
            session.close()
    
    def save_analysis_result(
        self,
        tool_name: str,
        analysis_type: str,
        result_data: Dict[str, Any]
    ) -> int:
        """
        Save analysis result to database
        
        Args:
            tool_name: Name of the tool
            analysis_type: Type of analysis ('pattern', 'idea', 'roadmap')
            result_data: Analysis result data
            
        Returns:
            ID of saved result
        """
        session = self.get_session()
        
        try:
            result = AnalysisResult(
                tool_name=tool_name,
                analysis_type=analysis_type,
                result_data=result_data
            )
            session.add(result)
            session.commit()
            
            logger.info("Analysis result saved", tool_name=tool_name, analysis_type=analysis_type)
            return result.id
            
        except Exception as e:
            session.rollback()
            logger.error("Error saving analysis result", error=str(e))
            raise
        finally:
            session.close()
    
    def get_analysis_results(
        self,
        tool_name: Optional[str] = None,
        analysis_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get analysis results from database
        
        Args:
            tool_name: Filter by tool name
            analysis_type: Filter by analysis type
            limit: Maximum number of results
            
        Returns:
            List of analysis result dictionaries
        """
        session = self.get_session()
        
        try:
            query = session.query(AnalysisResult)
            
            if tool_name:
                query = query.filter(AnalysisResult.tool_name == tool_name)
            
            if analysis_type:
                query = query.filter(AnalysisResult.analysis_type == analysis_type)
            
            query = query.order_by(AnalysisResult.created_at.desc()).limit(limit)
            
            results = []
            for result in query.all():
                results.append({
                    'id': result.id,
                    'tool_name': result.tool_name,
                    'analysis_type': result.analysis_type,
                    'result_data': result.result_data,
                    'created_at': result.created_at.isoformat()
                })
            
            return results
            
        finally:
            session.close()
