from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from app.repositories.watchlist_repo import TickerWatchlistRepository, OptionWatchlistRepository
from app.domain.models import TickerWatchlist, OptionWatchlist
from app.domain.errors import NotFoundError, ConflictError, DatabaseError


class SqlAlchemyTickerWatchlistRepository(TickerWatchlistRepository):
    """SQLAlchemy implementation of ticker watchlist repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[TickerWatchlist]:
        """Get all ticker watchlist entries"""
        try:
            stmt = select(TickerWatchlist).order_by(TickerWatchlist.symbol)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get tickers: {str(e)}")
    
    async def get_by_symbol(self, symbol: str) -> Optional[TickerWatchlist]:
        """Get ticker watchlist entry by symbol"""
        try:
            stmt = select(TickerWatchlist).where(TickerWatchlist.symbol == symbol.upper())
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get ticker {symbol}: {str(e)}")
    
    async def create(self, symbol: str, category: str = "Other") -> TickerWatchlist:
        """Create a new ticker watchlist entry"""
        try:
            ticker = TickerWatchlist(
                symbol=symbol.upper().strip(),
                category=category
            )
            self.session.add(ticker)
            await self.session.commit()
            await self.session.refresh(ticker)
            return ticker
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(f"Ticker {symbol} already exists in watchlist")
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create ticker {symbol}: {str(e)}")
    
    async def delete(self, symbol: str) -> bool:
        """Delete a ticker watchlist entry by symbol"""
        try:
            stmt = delete(TickerWatchlist).where(TickerWatchlist.symbol == symbol.upper())
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete ticker {symbol}: {str(e)}")
    
    async def get_symbols_only(self) -> List[str]:
        """Get just the ticker symbols for scanning"""
        try:
            stmt = select(TickerWatchlist.symbol).order_by(TickerWatchlist.symbol)
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get ticker symbols: {str(e)}")


class SqlAlchemyOptionWatchlistRepository(OptionWatchlistRepository):
    """SQLAlchemy implementation of option watchlist repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all(self) -> List[OptionWatchlist]:
        """Get all option watchlist entries"""
        try:
            stmt = select(OptionWatchlist).order_by(OptionWatchlist.added_at.desc())
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get options: {str(e)}")
    
    async def get_by_contract_symbol(self, contract_symbol: str) -> Optional[OptionWatchlist]:
        """Get option watchlist entry by contract symbol"""
        try:
            stmt = select(OptionWatchlist).where(
                OptionWatchlist.contract_symbol == contract_symbol
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            raise DatabaseError(f"Failed to get option {contract_symbol}: {str(e)}")
    
    async def create(
        self,
        contract_symbol: str,
        ticker: str,
        strike: float,
        expiry: str,
        option_type: str,
        notes: str = ""
    ) -> OptionWatchlist:
        """Create a new option watchlist entry"""
        try:
            option = OptionWatchlist(
                contract_symbol=contract_symbol,
                ticker=ticker.upper().strip(),
                strike=strike,
                expiry=expiry,
                option_type=option_type.upper(),
                notes=notes
            )
            self.session.add(option)
            await self.session.commit()
            await self.session.refresh(option)
            return option
        except IntegrityError:
            await self.session.rollback()
            raise ConflictError(f"Option {contract_symbol} already exists in watchlist")
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to create option {contract_symbol}: {str(e)}")
    
    async def delete(self, contract_symbol: str) -> bool:
        """Delete an option watchlist entry by contract symbol"""
        try:
            stmt = delete(OptionWatchlist).where(
                OptionWatchlist.contract_symbol == contract_symbol
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            await self.session.rollback()
            raise DatabaseError(f"Failed to delete option {contract_symbol}: {str(e)}")
    
    async def exists(self, contract_symbol: str) -> bool:
        """Check if option exists in watchlist"""
        try:
            stmt = select(OptionWatchlist).where(
                OptionWatchlist.contract_symbol == contract_symbol
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check option existence {contract_symbol}: {str(e)}")
